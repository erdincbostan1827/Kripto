from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from scripts.bounded_subprocess import run_captured_split

try:
    from scripts.operation_lock import operation_lock
except ModuleNotFoundError:
    from operation_lock import operation_lock

CONTRACT_FILE = "MIGRATION_COMPATIBILITY.json"
JOURNAL = ".database-migration.transaction.json"
RECEIPT_PREFIX = ".database-migration-receipt-"

RESTORE_RECEIPT_MAX_AGE_SECONDS = 86400
BACKUP_RECEIPT_MAX_AGE_SECONDS = 86400


def _environment_fingerprint(value: str) -> str:
    value = value.strip()
    if not value or len(value) > 128 or not re.fullmatch(r"[A-Za-z0-9._:-]+", value):
        raise RuntimeError("DATABASE_ENVIRONMENT_ID_INVALID")
    return hashlib.sha256(("ctp-environment-v1:" + value).encode()).hexdigest()


def _receipt_age_seconds(value: str, *, field: str) -> float:
    if not isinstance(value, str) or not value:
        raise RuntimeError(f"{field}_MISSING")
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise RuntimeError(f"{field}_INVALID") from exc
    if dt.tzinfo is None:
        raise RuntimeError(f"{field}_TIMEZONE_MISSING")
    age = (datetime.now(timezone.utc) - dt.astimezone(timezone.utc)).total_seconds()
    if age < -300:
        raise RuntimeError(f"{field}_FROM_FUTURE")
    return max(0.0, age)


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _canonical_hash(payload: dict) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _atomic_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2, sort_keys=True)
            fh.write("\n")
            fh.flush(); os.fsync(fh.fileno())
        os.replace(tmp_name, path)
    except BaseException:
        try: os.unlink(tmp_name)
        except FileNotFoundError: pass
        raise


def _migration_graph(root: Path) -> tuple[dict[str, str | None], str]:
    versions = root / "alembic" / "versions"
    if versions.is_symlink() or not versions.is_dir():
        raise RuntimeError("MIGRATION_VERSIONS_UNSAFE")
    revisions: dict[str, str | None] = {}
    for path in sorted(versions.glob("*.py")):
        if path.is_symlink() or not path.is_file():
            raise RuntimeError("MIGRATION_VERSION_FILE_UNSAFE")
        text = path.read_text(encoding="utf-8")
        rev = re.search(r"^revision\s*=\s*['\"]([^'\"]+)", text, re.M)
        down = re.search(r"^down_revision\s*=\s*(?:['\"]([^'\"]+)['\"]|None)", text, re.M)
        if rev:
            revision = rev.group(1)
            if revision in revisions:
                raise RuntimeError(f"MIGRATION_DUPLICATE_REVISION:{revision}")
            revisions[revision] = down.group(1) if down and down.group(1) else None
    if not revisions:
        raise RuntimeError("MIGRATION_REVISIONS_MISSING")
    referenced = {x for x in revisions.values() if x}
    heads = sorted(set(revisions) - referenced)
    if len(heads) != 1:
        raise RuntimeError(f"MIGRATION_HEAD_AMBIGUOUS:{heads}")
    for rev, down in revisions.items():
        if down is not None and down not in revisions:
            raise RuntimeError(f"MIGRATION_PARENT_MISSING:{rev}:{down}")
    return revisions, heads[0]


def _load_contract(root: Path, revisions: dict[str, str | None]) -> tuple[dict, str]:
    path = root / CONTRACT_FILE
    if path.is_symlink() or not path.is_file():
        raise RuntimeError("MIGRATION_COMPATIBILITY_CONTRACT_MISSING_OR_UNSAFE")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise RuntimeError(f"MIGRATION_COMPATIBILITY_CONTRACT_INVALID:{type(exc).__name__}") from exc
    if payload.get("schema_version") != "1.0" or payload.get("classification") != "DATABASE_MIGRATION_COMPATIBILITY_CONTRACT":
        raise RuntimeError("MIGRATION_COMPATIBILITY_CONTRACT_CLASSIFICATION_INVALID")
    entries = payload.get("migrations")
    if not isinstance(entries, dict):
        raise RuntimeError("MIGRATION_COMPATIBILITY_ENTRIES_INVALID")
    for rev, down in revisions.items():
        item = entries.get(rev)
        if not isinstance(item, dict):
            raise RuntimeError(f"MIGRATION_COMPATIBILITY_ENTRY_MISSING:{rev}")
        if item.get("down_revision") != down:
            raise RuntimeError(f"MIGRATION_COMPATIBILITY_PARENT_MISMATCH:{rev}")
        if item.get("previous_release_compatible") not in {True, False}:
            raise RuntimeError(f"MIGRATION_COMPATIBILITY_PREVIOUS_RELEASE_INVALID:{rev}")
        if item.get("requires_backup") not in {True, False}:
            raise RuntimeError(f"MIGRATION_COMPATIBILITY_BACKUP_POLICY_INVALID:{rev}")
        if item.get("rollback_strategy") not in {"restore_only", "restore_or_forward", "forward_only"}:
            raise RuntimeError(f"MIGRATION_COMPATIBILITY_ROLLBACK_STRATEGY_INVALID:{rev}")
    return payload, _sha256_file(path)


def migration_state(root: Path) -> dict:
    revisions, head = _migration_graph(root)
    contract, contract_hash = _load_contract(root, revisions)
    return {"head": head, "revisions": revisions, "contract": contract, "contract_sha256": contract_hash}


def _path_to_ancestor(revisions: dict[str, str | None], ancestor: str, descendant: str) -> list[str]:
    cur = descendant; reverse: list[str] = []
    seen: set[str] = set()
    while cur != ancestor:
        if cur in seen or cur not in revisions:
            raise RuntimeError("MIGRATION_LINEAGE_INVALID")
        seen.add(cur); reverse.append(cur)
        parent = revisions[cur]
        if parent is None:
            raise RuntimeError(f"MIGRATION_NOT_DESCENDANT:{ancestor}:{descendant}")
        cur = parent
    return list(reversed(reverse))


def compare_release_migrations(active: Path, candidate: Path) -> dict:
    before = migration_state(active); after = migration_state(candidate)
    if before["head"] == after["head"]:
        return {"required": False, "from_head": before["head"], "to_head": after["head"], "pending": [], "previous_release_compatible": True, "requires_backup": False, "target_contract_sha256": after["contract_sha256"]}
    # Candidate must contain the active head and the target must descend from it.
    if before["head"] not in after["revisions"]:
        raise RuntimeError("MIGRATION_ACTIVE_HEAD_NOT_IN_CANDIDATE")
    pending = _path_to_ancestor(after["revisions"], before["head"], after["head"])
    entries = after["contract"]["migrations"]
    compat = all(entries[x]["previous_release_compatible"] is True for x in pending)
    backup = any(entries[x]["requires_backup"] is True for x in pending)
    if not compat:
        raise RuntimeError(f"MIGRATION_PREVIOUS_RELEASE_INCOMPATIBLE:{pending}")
    return {"required": True, "from_head": before["head"], "to_head": after["head"], "pending": pending, "previous_release_compatible": compat, "requires_backup": backup, "target_contract_sha256": after["contract_sha256"]}


def verify_restore_drill_receipt(path: Path, *, expected_backup_sha256: str, expected_environment_id: str | None = None, max_age_seconds: int = RESTORE_RECEIPT_MAX_AGE_SECONDS) -> dict:
    if path.is_symlink() or not path.is_file():
        raise RuntimeError("DATABASE_RESTORE_DRILL_RECEIPT_MISSING_OR_UNSAFE")
    raw = path.read_bytes(); digest = hashlib.sha256(raw).hexdigest()
    try: payload = json.loads(raw)
    except Exception as exc: raise RuntimeError(f"DATABASE_RESTORE_DRILL_RECEIPT_INVALID:{type(exc).__name__}") from exc
    if payload.get("schema_version") not in {"1.0", "1.1"} or payload.get("classification") != "VERIFIED_DATABASE_RESTORE_DRILL_RECEIPT":
        raise RuntimeError("DATABASE_RESTORE_DRILL_RECEIPT_CONTRACT_INVALID")
    provenance = payload.get("provenance_sha256"); body = dict(payload); body.pop("provenance_sha256", None)
    if provenance != _canonical_hash(body):
        raise RuntimeError("DATABASE_RESTORE_DRILL_RECEIPT_PROVENANCE_MISMATCH")
    if payload.get("backup_sha256") != expected_backup_sha256:
        raise RuntimeError("DATABASE_RESTORE_DRILL_BACKUP_HASH_MISMATCH")
    if payload.get("restore_status") != "PASS":
        raise RuntimeError("DATABASE_RESTORE_DRILL_NOT_PASS")
    if not isinstance(payload.get("restored_table_count"), int) or payload["restored_table_count"] <= 0:
        raise RuntimeError("DATABASE_RESTORE_DRILL_TABLE_COUNT_INVALID")
    environment_fingerprint = None
    age_seconds = None
    if payload.get("schema_version") == "1.1":
        env_id = payload.get("environment_id")
        environment_fingerprint = payload.get("environment_fingerprint")
        if not isinstance(env_id, str) or environment_fingerprint != _environment_fingerprint(env_id):
            raise RuntimeError("DATABASE_RESTORE_DRILL_ENVIRONMENT_FINGERPRINT_MISMATCH")
        if expected_environment_id is not None and environment_fingerprint != _environment_fingerprint(expected_environment_id):
            raise RuntimeError("DATABASE_RESTORE_DRILL_ENVIRONMENT_MISMATCH")
        age_seconds = _receipt_age_seconds(payload.get("completed_at"), field="DATABASE_RESTORE_DRILL_COMPLETED_AT")
        if max_age_seconds < 1 or age_seconds > max_age_seconds:
            raise RuntimeError("DATABASE_RESTORE_DRILL_RECEIPT_STALE")
    elif expected_environment_id is not None:
        raise RuntimeError("DATABASE_RESTORE_DRILL_ENVIRONMENT_BINDING_REQUIRED")
    return {"verified": True, "receipt_sha256": digest, "provenance_sha256": provenance, "environment_fingerprint": environment_fingerprint, "age_seconds": age_seconds}


def verify_backup_receipt(path: Path, *, expected_head: str, expected_active_tree_sha256: str, expected_environment_id: str | None = None, max_age_seconds: int = BACKUP_RECEIPT_MAX_AGE_SECONDS) -> dict:
    if path.is_symlink() or not path.is_file():
        raise RuntimeError("DATABASE_BACKUP_RECEIPT_MISSING_OR_UNSAFE")
    raw = path.read_bytes(); digest = hashlib.sha256(raw).hexdigest()
    try: payload = json.loads(raw)
    except Exception as exc: raise RuntimeError(f"DATABASE_BACKUP_RECEIPT_INVALID:{type(exc).__name__}") from exc
    if payload.get("schema_version") not in {"1.0", "1.1"} or payload.get("classification") != "VERIFIED_DATABASE_BACKUP_RECEIPT":
        raise RuntimeError("DATABASE_BACKUP_RECEIPT_CONTRACT_INVALID")
    if payload.get("schema_version") == "1.1":
        provenance = payload.get("provenance_sha256"); body = dict(payload); body.pop("provenance_sha256", None)
        if provenance != _canonical_hash(body):
            raise RuntimeError("DATABASE_BACKUP_RECEIPT_PROVENANCE_MISMATCH")
        env_id = payload.get("environment_id")
        env_fp = payload.get("environment_fingerprint")
        if not isinstance(env_id, str) or env_fp != _environment_fingerprint(env_id):
            raise RuntimeError("DATABASE_BACKUP_RECEIPT_ENVIRONMENT_FINGERPRINT_MISMATCH")
        if expected_environment_id is not None and env_fp != _environment_fingerprint(expected_environment_id):
            raise RuntimeError("DATABASE_BACKUP_RECEIPT_ENVIRONMENT_MISMATCH")
        age = _receipt_age_seconds(payload.get("created_at"), field="DATABASE_BACKUP_RECEIPT_CREATED_AT")
        if max_age_seconds < 1 or age > max_age_seconds:
            raise RuntimeError("DATABASE_BACKUP_RECEIPT_STALE")
    elif expected_environment_id is not None:
        raise RuntimeError("DATABASE_BACKUP_RECEIPT_ENVIRONMENT_BINDING_REQUIRED")
    if payload.get("migration_head") != expected_head:
        raise RuntimeError("DATABASE_BACKUP_RECEIPT_MIGRATION_HEAD_MISMATCH")
    if payload.get("active_tree_sha256") != expected_active_tree_sha256:
        raise RuntimeError("DATABASE_BACKUP_RECEIPT_ACTIVE_TREE_MISMATCH")
    artifact = payload.get("backup_artifact")
    expected_hash = payload.get("backup_sha256")
    if not isinstance(artifact, str) or not isinstance(expected_hash, str) or len(expected_hash) != 64:
        raise RuntimeError("DATABASE_BACKUP_RECEIPT_ARTIFACT_FIELDS_INVALID")
    artifact_path = (path.parent / artifact).resolve(strict=False) if not Path(artifact).is_absolute() else Path(artifact).resolve(strict=False)
    if artifact_path.is_symlink() or not artifact_path.is_file():
        raise RuntimeError("DATABASE_BACKUP_ARTIFACT_MISSING_OR_UNSAFE")
    if _sha256_file(artifact_path) != expected_hash:
        raise RuntimeError("DATABASE_BACKUP_ARTIFACT_HASH_MISMATCH")
    restore_ref = payload.get("restore_drill_receipt")
    if not isinstance(restore_ref, str) or not restore_ref or Path(restore_ref).name != restore_ref:
        raise RuntimeError("DATABASE_BACKUP_RESTORE_DRILL_REFERENCE_INVALID")
    restore_path = path.parent / restore_ref
    restore = verify_restore_drill_receipt(restore_path, expected_backup_sha256=expected_hash, expected_environment_id=expected_environment_id)
    expected_restore_hash = payload.get("restore_drill_receipt_sha256")
    if expected_restore_hash != _sha256_file(restore_path):
        raise RuntimeError("DATABASE_BACKUP_RESTORE_DRILL_RECEIPT_HASH_MISMATCH")
    return {"verified": True, "receipt_sha256": digest, "backup_sha256": expected_hash, "migration_head": expected_head, "restore_drill_receipt_sha256": restore["receipt_sha256"], "restore_drill_provenance_sha256": restore["provenance_sha256"], "environment_fingerprint": restore.get("environment_fingerprint")}


def _run_argv(command: list[str], *, cwd: Path, timeout_seconds: int) -> subprocess.CompletedProcess[str]:
    if not isinstance(command, list) or not command or any(not isinstance(x, str) or not x or "\x00" in x for x in command):
        raise RuntimeError("DATABASE_MIGRATION_COMMAND_INVALID")
    if not 1 <= timeout_seconds <= 1800:
        raise RuntimeError("DATABASE_MIGRATION_TIMEOUT_INVALID")
    return run_captured_split(command, cwd=cwd, timeout=timeout_seconds)


def probe_database_head(command: list[str], *, cwd: Path, timeout_seconds: int = 60) -> str:
    try: proc = _run_argv(command, cwd=cwd, timeout_seconds=timeout_seconds)
    except subprocess.TimeoutExpired as exc: raise RuntimeError("DATABASE_MIGRATION_PROBE_TIMEOUT") from exc
    if proc.returncode != 0:
        raise RuntimeError(f"DATABASE_MIGRATION_PROBE_FAILED:{proc.returncode}")
    head = proc.stdout.strip()
    if not re.fullmatch(r"[A-Za-z0-9_.-]{1,128}", head):
        raise RuntimeError("DATABASE_MIGRATION_PROBE_OUTPUT_INVALID")
    return head


def _journal_path(state_dir: Path) -> Path: return state_dir / JOURNAL


def _read_journal(state_dir: Path) -> dict:
    path = _journal_path(state_dir)
    if path.is_symlink() or not path.is_file(): raise RuntimeError("DATABASE_MIGRATION_JOURNAL_UNSAFE")
    try: payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc: raise RuntimeError(f"DATABASE_MIGRATION_JOURNAL_INVALID:{type(exc).__name__}") from exc
    if payload.get("schema_version") != "1.0" or payload.get("classification") != "DATABASE_MIGRATION_TRANSACTION":
        raise RuntimeError("DATABASE_MIGRATION_JOURNAL_CONTRACT_INVALID")
    return payload


def _finalize_receipt(state_dir: Path, journal: dict, observed_head: str) -> Path:
    body = {
        "schema_version": "1.0", "classification": "VERIFIED_DATABASE_MIGRATION_RECEIPT",
        "transaction_id": journal["transaction_id"], "from_head": journal["from_head"], "to_head": journal["to_head"],
        "observed_head": observed_head, "active_tree_sha256": journal["active_tree_sha256"],
        "candidate_tree_sha256": journal["candidate_tree_sha256"], "candidate_git_commit_sha": journal.get("candidate_git_commit_sha"),
        "compatibility_contract_sha256": journal["compatibility_contract_sha256"],
        "database_backup_receipt_sha256": journal["database_backup_receipt_sha256"], "database_restore_drill_receipt_sha256": journal.get("database_restore_drill_receipt_sha256"), "database_restore_drill_provenance_sha256": journal.get("database_restore_drill_provenance_sha256"), "database_environment_fingerprint": journal.get("database_environment_fingerprint"),
        "pending_revisions": journal["pending_revisions"], "completed_at": datetime.now(timezone.utc).isoformat(),
    }
    body["provenance_sha256"] = _canonical_hash(body)
    path = state_dir / f"{RECEIPT_PREFIX}{journal['transaction_id']}.json"
    _atomic_json(path, body); return path


def recover_migration_transaction(*, state_dir: Path, probe_command: list[str], cwd: Path, timeout_seconds: int = 60) -> dict:
    path = _journal_path(state_dir)
    if not path.exists() and not path.is_symlink(): return {"recovered": False, "status": "NO_TRANSACTION"}
    journal = _read_journal(state_dir)
    observed = probe_database_head(probe_command, cwd=cwd, timeout_seconds=timeout_seconds)
    if observed == journal["from_head"]:
        path.unlink(); return {"recovered": True, "status": "MIGRATION_NOT_APPLIED", "observed_head": observed}
    if observed == journal["to_head"]:
        receipt = _finalize_receipt(state_dir, journal, observed); path.unlink()
        return {"recovered": True, "status": "MIGRATION_COMPLETED_BEFORE_INTERRUPTION", "observed_head": observed, "migration_receipt": str(receipt)}
    raise RuntimeError(f"DATABASE_MIGRATION_STATE_AMBIGUOUS:{observed}")


def run_guarded_migration(*, active: Path, candidate: Path, state_dir: Path, backup_receipt: Path, probe_command: list[str], migration_command: list[str], candidate_git_commit_sha: str | None = None, environment_id: str | None = None, timeout_seconds: int = 300, _lock_held: bool = False) -> dict:
    active = active.resolve(); candidate = candidate.resolve()
    if not _lock_held:
        with operation_lock(active.parent, operation="database-migration"):
            return run_guarded_migration(active=active, candidate=candidate, state_dir=state_dir, backup_receipt=backup_receipt, probe_command=probe_command, migration_command=migration_command, candidate_git_commit_sha=candidate_git_commit_sha, environment_id=environment_id, timeout_seconds=timeout_seconds, _lock_held=True)
    state_dir = state_dir.resolve(); state_dir.mkdir(parents=True, exist_ok=True)
    if state_dir.is_symlink(): raise RuntimeError("DATABASE_MIGRATION_STATE_DIR_UNSAFE")
    try:
        from scripts.deployment_transaction_state import assert_no_conflicting_journals
    except ModuleNotFoundError:
        from deployment_transaction_state import assert_no_conflicting_journals
    assert_no_conflicting_journals(state_dir, allowed={"database_migration"})
    recovery = recover_migration_transaction(state_dir=state_dir, probe_command=probe_command, cwd=candidate, timeout_seconds=min(timeout_seconds, 60))
    plan = compare_release_migrations(active, candidate)
    if not plan["required"]:
        return {"classification": "GUARDED_DATABASE_MIGRATION", "migrated": False, "status": "NO_MIGRATION_REQUIRED", "plan": plan, "recovery": recovery}
    # Import lazily to avoid a circular dependency at module import time.
    try:
        from scripts.transactional_release_update import _tree_sha256
    except ModuleNotFoundError:
        from transactional_release_update import _tree_sha256
    active_hash = _tree_sha256(active); candidate_hash = _tree_sha256(candidate)
    backup = verify_backup_receipt(backup_receipt, expected_head=plan["from_head"], expected_active_tree_sha256=active_hash, expected_environment_id=environment_id)
    observed_before = probe_database_head(probe_command, cwd=candidate, timeout_seconds=min(timeout_seconds, 60))
    if observed_before != plan["from_head"]:
        raise RuntimeError(f"DATABASE_MIGRATION_PRE_HEAD_MISMATCH:{observed_before}:{plan['from_head']}")
    token = uuid.uuid4().hex
    journal = {
        "schema_version": "1.0", "classification": "DATABASE_MIGRATION_TRANSACTION", "transaction_id": token,
        "created_at": datetime.now(timezone.utc).isoformat(), "status": "PREPARED", "from_head": plan["from_head"], "to_head": plan["to_head"],
        "pending_revisions": plan["pending"], "previous_release_compatible": plan["previous_release_compatible"],
        "active_tree_sha256": active_hash, "candidate_tree_sha256": candidate_hash, "candidate_git_commit_sha": candidate_git_commit_sha,
        "compatibility_contract_sha256": plan["target_contract_sha256"], "database_backup_receipt_sha256": backup["receipt_sha256"], "database_restore_drill_receipt_sha256": backup["restore_drill_receipt_sha256"], "database_restore_drill_provenance_sha256": backup["restore_drill_provenance_sha256"], "database_environment_fingerprint": backup.get("environment_fingerprint"),
        "policy": "FAIL_CLOSED_ON_AMBIGUOUS_DATABASE_HEAD; NEVER_INFER_DESTRUCTIVE_DOWNGRADE",
    }
    _atomic_json(_journal_path(state_dir), journal)
    try:
        proc = _run_argv(migration_command, cwd=candidate, timeout_seconds=timeout_seconds)
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError("DATABASE_MIGRATION_COMMAND_TIMEOUT_RECOVERY_REQUIRED") from exc
    if proc.returncode != 0:
        # Preserve the journal. The next recovery probes authoritative DB state.
        raise RuntimeError(f"DATABASE_MIGRATION_COMMAND_FAILED_RECOVERY_REQUIRED:{proc.returncode}")
    _atomic_json(_journal_path(state_dir), {**journal, "status": "COMMAND_COMPLETED"})
    observed_after = probe_database_head(probe_command, cwd=candidate, timeout_seconds=min(timeout_seconds, 60))
    if observed_after != plan["to_head"]:
        raise RuntimeError(f"DATABASE_MIGRATION_POST_HEAD_MISMATCH_RECOVERY_REQUIRED:{observed_after}:{plan['to_head']}")
    receipt = _finalize_receipt(state_dir, journal, observed_after)
    try:
        from scripts.deployment_audit_chain import append_event
    except ModuleNotFoundError:
        from deployment_audit_chain import append_event
    audit_event = append_event(active.parent, event_type="DATABASE_MIGRATION_COMMITTED", subjects={
        "migration_receipt": receipt.name,
        "migration_receipt_sha256": _sha256_file(receipt),
        "from_head": plan["from_head"],
        "to_head": plan["to_head"],
        "candidate_tree_sha256": candidate_hash,
    })
    _journal_path(state_dir).unlink()
    return {"classification": "GUARDED_DATABASE_MIGRATION", "migrated": True, "status": "MIGRATION_COMMITTED", "plan": plan, "recovery": recovery, "migration_receipt": str(receipt), "migration_receipt_sha256": _sha256_file(receipt), "deployment_audit_event_sha256": audit_event["event_sha256"]}


def verify_migration_receipt(path: Path, *, active_tree_sha256: str, candidate_tree_sha256: str, from_head: str, to_head: str, candidate_git_commit_sha: str | None = None) -> dict:
    if path.is_symlink() or not path.is_file(): raise RuntimeError("DATABASE_MIGRATION_RECEIPT_MISSING_OR_UNSAFE")
    raw = path.read_bytes(); digest = hashlib.sha256(raw).hexdigest()
    try: payload = json.loads(raw)
    except Exception as exc: raise RuntimeError(f"DATABASE_MIGRATION_RECEIPT_INVALID:{type(exc).__name__}") from exc
    if payload.get("schema_version") != "1.0" or payload.get("classification") != "VERIFIED_DATABASE_MIGRATION_RECEIPT": raise RuntimeError("DATABASE_MIGRATION_RECEIPT_CONTRACT_INVALID")
    provenance = payload.get("provenance_sha256"); body = dict(payload); body.pop("provenance_sha256", None)
    if provenance != _canonical_hash(body): raise RuntimeError("DATABASE_MIGRATION_RECEIPT_PROVENANCE_MISMATCH")
    expected = {"active_tree_sha256": active_tree_sha256, "candidate_tree_sha256": candidate_tree_sha256, "from_head": from_head, "to_head": to_head, "observed_head": to_head}
    for key, value in expected.items():
        if payload.get(key) != value: raise RuntimeError(f"DATABASE_MIGRATION_RECEIPT_{key.upper()}_MISMATCH")
    if candidate_git_commit_sha is not None and payload.get("candidate_git_commit_sha") != candidate_git_commit_sha: raise RuntimeError("DATABASE_MIGRATION_RECEIPT_GIT_IDENTITY_MISMATCH")
    return {"verified": True, "receipt_sha256": digest, "provenance_sha256": provenance}


def main() -> int:
    p = argparse.ArgumentParser(description="Fail-closed database migration transaction with backup and authoritative head recovery.")
    p.add_argument("--active", type=Path, required=True); p.add_argument("--candidate", type=Path, required=True); p.add_argument("--state-dir", type=Path, required=True)
    p.add_argument("--probe-command-json", required=True); p.add_argument("--migration-command-json"); p.add_argument("--backup-receipt", type=Path); p.add_argument("--environment-id", default=os.environ.get("CTP_ENVIRONMENT_ID")); p.add_argument("--recover-only", action="store_true"); p.add_argument("--timeout-seconds", type=int, default=300)
    args = p.parse_args(); probe = json.loads(args.probe_command_json)
    if args.recover_only:
        result = recover_migration_transaction(state_dir=args.state_dir, probe_command=probe, cwd=args.candidate, timeout_seconds=min(args.timeout_seconds, 60))
    else:
        if args.backup_receipt is None or not args.migration_command_json: raise SystemExit("DATABASE_MIGRATION_BACKUP_AND_COMMAND_REQUIRED")
        if not args.environment_id: raise SystemExit("DATABASE_MIGRATION_ENVIRONMENT_ID_REQUIRED")
        result = run_guarded_migration(active=args.active, candidate=args.candidate, state_dir=args.state_dir, backup_receipt=args.backup_receipt, probe_command=probe, migration_command=json.loads(args.migration_command_json), environment_id=args.environment_id, timeout_seconds=args.timeout_seconds)
    print(json.dumps(result, sort_keys=True)); return 0

if __name__ == "__main__": raise SystemExit(main())
