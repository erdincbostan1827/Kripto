from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path

try:
    from scripts.operation_lock import operation_lock
except ModuleNotFoundError:
    from operation_lock import operation_lock

try:
    from scripts.extract_source_package import extract
    from scripts.verify_source_package_identity import verify_source_package_identity
except ModuleNotFoundError:
    from extract_source_package import extract
    from verify_source_package_identity import verify_source_package_identity

JOURNAL = ".release-update.transaction.json"
CANDIDATE_PREFIX = ".release-update-candidate-"
BACKUP_PREFIX = ".release-update-rollback-"
FAILED_PREFIX = ".release-update-failed-"
RECEIPT_SUFFIX = ".receipt.json"
ACCEPTANCE_PREFIX = ".release-update-acceptance-"
ROLLBACK_ACCEPTANCE_PREFIX = ".release-rollback-acceptance-"



def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _canonical_hash(payload: dict) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def _tree_sha256(root: Path) -> str:
    if root.is_symlink() or not root.is_dir():
        raise RuntimeError("UPDATE_TREE_UNSAFE")
    h = hashlib.sha256()
    for path in sorted(root.rglob("*"), key=lambda x: x.relative_to(root).as_posix()):
        rel = path.relative_to(root).as_posix()
        if path.is_symlink():
            raise RuntimeError(f"UPDATE_TREE_SYMLINK:{rel}")
        if path.is_file():
            h.update(rel.encode("utf-8") + b"\0")
            h.update(str(path.stat().st_size).encode("ascii") + b"\0")
            h.update(_sha256_file(path).encode("ascii") + b"\n")
    return h.hexdigest()


def _alembic_head(root: Path) -> str:
    versions = root / "alembic" / "versions"
    revisions: dict[str, str | None] = {}
    if not versions.is_dir() or versions.is_symlink():
        raise RuntimeError("UPDATE_ALEMBIC_VERSIONS_UNSAFE")
    import re
    for path in versions.glob("*.py"):
        text = path.read_text(encoding="utf-8")
        rev = re.search(r"^revision\s*=\s*['\"]([^'\"]+)", text, re.M)
        down = re.search(r"^down_revision\s*=\s*(?:['\"]([^'\"]+)['\"]|None)", text, re.M)
        if rev:
            revisions[rev.group(1)] = down.group(1) if down and down.group(1) else None
    if not revisions:
        raise RuntimeError("UPDATE_ALEMBIC_REVISIONS_MISSING")
    referenced = {d for d in revisions.values() if d}
    heads = sorted(set(revisions) - referenced)
    if len(heads) != 1:
        raise RuntimeError(f"UPDATE_ALEMBIC_HEAD_AMBIGUOUS:{heads}")
    return heads[0]


def verify_runtime_binding(root: Path) -> dict:
    identity = verify_source_package_identity(root)
    problems: list[str] = []
    if not identity.get("verified"):
        problems.append("SOURCE_IDENTITY_INVALID")
    manifest_path = root / "RELEASE_MANIFEST.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"accepted": False, "problems": [f"RELEASE_MANIFEST_INVALID:{type(exc).__name__}"]}
    if manifest.get("git_commit_sha") != identity.get("git_commit_sha"):
        problems.append("RELEASE_PACKAGE_GIT_IDENTITY_MISMATCH")
    try:
        head = _alembic_head(root)
        if manifest.get("migration_version") != head:
            problems.append("RELEASE_MIGRATION_HEAD_MISMATCH")
    except RuntimeError as exc:
        problems.append(str(exc))
        head = None
    arch = root / "architecture_profile.yaml"
    if not arch.is_file() or arch.is_symlink():
        problems.append("ARCHITECTURE_PROFILE_UNSAFE")
        arch_hash = None
    else:
        arch_hash = _sha256_file(arch)
        if manifest.get("architecture_profile_hash") != arch_hash:
            problems.append("RELEASE_ARCHITECTURE_PROFILE_HASH_MISMATCH")
    return {
        "accepted": not problems,
        "classification": "POST_CUTOVER_STATIC_RUNTIME_BINDING",
        "git_commit_sha": identity.get("git_commit_sha"),
        "migration_version": head,
        "architecture_profile_hash": arch_hash,
        "problems": sorted(set(problems)),
    }


def run_post_cutover_acceptance(root: Path, *, command: list[str] | None = None, timeout_seconds: int = 60) -> dict:
    binding = verify_runtime_binding(root)
    result = {"accepted": bool(binding.get("accepted")), "binding": binding, "runtime_command": None, "problems": list(binding.get("problems", []))}
    if not result["accepted"] or command is None:
        return result
    if not isinstance(command, list) or not command or any(not isinstance(x, str) or not x or "\x00" in x for x in command):
        raise RuntimeError("UPDATE_ACCEPTANCE_COMMAND_INVALID")
    if timeout_seconds < 1 or timeout_seconds > 900:
        raise RuntimeError("UPDATE_ACCEPTANCE_TIMEOUT_INVALID")
    try:
        proc = subprocess.run(command, cwd=root, shell=False, text=True, capture_output=True, timeout=timeout_seconds, check=False)
        cmd_result = {
            "executed": True, "returncode": proc.returncode,
            "stdout_tail": proc.stdout[-4000:], "stderr_tail": proc.stderr[-4000:],
            "shell": False,
        }
    except subprocess.TimeoutExpired as exc:
        cmd_result = {"executed": True, "timed_out": True, "timeout_seconds": timeout_seconds, "shell": False}
        result["problems"].append("POST_CUTOVER_RUNTIME_COMMAND_TIMEOUT")
        result["runtime_command"] = cmd_result
        result["accepted"] = False
        return result
    result["runtime_command"] = cmd_result
    if proc.returncode != 0:
        result["problems"].append(f"POST_CUTOVER_RUNTIME_COMMAND_FAILED:{proc.returncode}")
        result["accepted"] = False
    return result


def _acceptance_receipt_path(parent: Path, token: str) -> Path:
    return parent / f"{ACCEPTANCE_PREFIX}{token}.json"


def _write_acceptance_receipt(*, parent: Path, token: str, pre_tree_sha256: str, post_tree_sha256: str, post_identity: dict, binding: dict, migration_receipt_verification: dict | None) -> Path:
    path = _acceptance_receipt_path(parent, token)
    body = {
        "schema_version": "1.0",
        "classification": "VERIFIED_RELEASE_UPDATE_ACCEPTANCE_RECEIPT",
        "transaction_id": token,
        "pre_update_tree_sha256": pre_tree_sha256,
        "post_update_tree_sha256": post_tree_sha256,
        "post_update_git_commit_sha": post_identity.get("git_commit_sha"),
        "migration_version": binding.get("migration_version"),
        "architecture_profile_hash": binding.get("architecture_profile_hash"),
        "migration_receipt_sha256": (migration_receipt_verification or {}).get("receipt_sha256"),
        "migration_receipt_provenance_sha256": (migration_receipt_verification or {}).get("provenance_sha256"),
        "accepted_at": datetime.now(timezone.utc).isoformat(),
        "policy": "STATIC_BINDING_AND_OPTIONAL_GUARDED_DATABASE_MIGRATION_PROVENANCE_ACCEPTED",
    }
    body["provenance_sha256"] = _canonical_hash(body)
    _atomic_json(path, body)
    return path


def _verify_acceptance_receipt(path: Path) -> dict:
    if path.is_symlink() or not path.is_file():
        raise RuntimeError("UPDATE_ACCEPTANCE_RECEIPT_MISSING_OR_UNSAFE")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise RuntimeError(f"UPDATE_ACCEPTANCE_RECEIPT_INVALID:{type(exc).__name__}") from exc
    if payload.get("schema_version") != "1.0" or payload.get("classification") != "VERIFIED_RELEASE_UPDATE_ACCEPTANCE_RECEIPT":
        raise RuntimeError("UPDATE_ACCEPTANCE_RECEIPT_CONTRACT_INVALID")
    provenance = payload.get("provenance_sha256")
    body = dict(payload); body.pop("provenance_sha256", None)
    if provenance != _canonical_hash(body):
        raise RuntimeError("UPDATE_ACCEPTANCE_RECEIPT_PROVENANCE_MISMATCH")
    return payload


def _receipt_path(backup: Path) -> Path:
    return backup.parent / f"{backup.name}{RECEIPT_SUFFIX}"


def _write_rollback_receipt(*, backup: Path, pre_hash: str, post_identity: dict, binding: dict, acceptance_receipt: Path) -> Path:
    receipt = _receipt_path(backup)
    payload = {
        "schema_version": "1.0",
        "classification": "VERIFIED_RELEASE_ROLLBACK_RECEIPT",
        "backup": backup.name,
        "backup_tree_sha256": pre_hash,
        "post_update_git_commit_sha": post_identity.get("git_commit_sha"),
        "post_update_binding": binding,
        "acceptance_receipt": acceptance_receipt.name,
        "acceptance_receipt_sha256": _sha256_file(acceptance_receipt),
    }
    _atomic_json(receipt, payload)
    return receipt


def _verify_rollback_receipt(backup: Path) -> dict:
    receipt = _receipt_path(backup)
    if receipt.is_symlink() or not receipt.is_file():
        raise RuntimeError("ROLLBACK_RECEIPT_MISSING_OR_UNSAFE")
    try:
        payload = json.loads(receipt.read_text(encoding="utf-8"))
    except Exception as exc:
        raise RuntimeError(f"ROLLBACK_RECEIPT_INVALID:{type(exc).__name__}") from exc
    if payload.get("schema_version") != "1.0" or payload.get("classification") != "VERIFIED_RELEASE_ROLLBACK_RECEIPT":
        raise RuntimeError("ROLLBACK_RECEIPT_CONTRACT_INVALID")
    if payload.get("backup") != backup.name:
        raise RuntimeError("ROLLBACK_RECEIPT_BACKUP_MISMATCH")
    actual = _tree_sha256(backup)
    if payload.get("backup_tree_sha256") != actual:
        raise RuntimeError("ROLLBACK_BACKUP_HASH_MISMATCH")
    acceptance_name = payload.get("acceptance_receipt")
    if not isinstance(acceptance_name, str) or not acceptance_name.startswith(ACCEPTANCE_PREFIX) or Path(acceptance_name).name != acceptance_name:
        raise RuntimeError("ROLLBACK_ACCEPTANCE_RECEIPT_REFERENCE_INVALID")
    acceptance_path = backup.parent / acceptance_name
    _verify_acceptance_receipt(acceptance_path)
    if payload.get("acceptance_receipt_sha256") != _sha256_file(acceptance_path):
        raise RuntimeError("ROLLBACK_ACCEPTANCE_RECEIPT_HASH_MISMATCH")
    return payload

def _atomic_json(path: Path, payload: dict) -> None:
    fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2, sort_keys=True)
            fh.write("\n")
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp_name, path)
    except BaseException:
        try:
            os.unlink(tmp_name)
        except FileNotFoundError:
            pass
        raise


def _safe_sibling(parent: Path, raw: object, prefix: str) -> Path:
    if not isinstance(raw, str) or not raw:
        raise RuntimeError("UPDATE_TRANSACTION_PATH_INVALID")
    candidate = Path(raw)
    if candidate.is_absolute():
        resolved = candidate.resolve(strict=False)
    else:
        resolved = (parent / candidate).resolve(strict=False)
    if resolved.parent != parent.resolve() or not resolved.name.startswith(prefix):
        raise RuntimeError("UPDATE_TRANSACTION_PATH_OUTSIDE_PARENT")
    if resolved.is_symlink():
        raise RuntimeError("UPDATE_TRANSACTION_PATH_SYMLINK")
    return resolved


def _validate_active(active: Path) -> None:
    if active.is_symlink() or not active.is_dir():
        raise RuntimeError("UPDATE_ACTIVE_DIRECTORY_UNSAFE")
    if active.parent.resolve() == active.resolve():
        raise RuntimeError("UPDATE_ACTIVE_DIRECTORY_INVALID")


def _journal_path(parent: Path) -> Path:
    return parent / JOURNAL


def _read_journal(parent: Path) -> dict:
    path = _journal_path(parent)
    if path.is_symlink() or not path.is_file():
        raise RuntimeError("UPDATE_TRANSACTION_JOURNAL_UNSAFE")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise RuntimeError(f"UPDATE_TRANSACTION_JOURNAL_INVALID:{type(exc).__name__}") from exc
    if payload.get("schema_version") != "1.0" or payload.get("classification") != "RELEASE_UPDATE_TRANSACTION":
        raise RuntimeError("UPDATE_TRANSACTION_JOURNAL_CONTRACT_INVALID")
    return payload


def recover_incomplete_update(*, active: Path) -> dict:
    parent = active.parent.resolve()
    journal_path = _journal_path(parent)
    if not journal_path.exists() and not journal_path.is_symlink():
        return {"recovered": False, "status": "NO_TRANSACTION"}
    journal = _read_journal(parent)
    expected_active = journal.get("active_name")
    if expected_active != active.name:
        raise RuntimeError("UPDATE_TRANSACTION_ACTIVE_MISMATCH")
    backup = _safe_sibling(parent, journal.get("backup"), BACKUP_PREFIX)
    candidate = _safe_sibling(parent, journal.get("candidate"), CANDIDATE_PREFIX)
    status = journal.get("status")

    # Any surviving journal means cutover did not reach an authoritative commit.
    # Prefer the exact pre-update tree and never guess that a candidate is safe.
    if backup.exists():
        if backup.is_symlink() or not backup.is_dir():
            raise RuntimeError("UPDATE_TRANSACTION_BACKUP_UNSAFE")
        if active.exists():
            failed = parent / f"{FAILED_PREFIX}{uuid.uuid4().hex}"
            os.replace(active, failed)
            try:
                os.replace(backup, active)
            except BaseException:
                os.replace(failed, active)
                raise
            shutil.rmtree(failed, ignore_errors=True)
        else:
            os.replace(backup, active)
    elif status not in {"PREPARED"}:
        raise RuntimeError("UPDATE_TRANSACTION_BACKUP_MISSING")

    if candidate.exists():
        shutil.rmtree(candidate, ignore_errors=True)
    _receipt_path(backup).unlink(missing_ok=True)
    journal_path.unlink()
    _validate_active(active)
    return {"recovered": True, "status": "ROLLED_BACK_INTERRUPTED_UPDATE"}


def _single_project_root(extraction_dir: Path) -> Path:
    children = [p for p in extraction_dir.iterdir()]
    if len(children) != 1 or not children[0].is_dir() or children[0].is_symlink():
        raise RuntimeError("UPDATE_SOURCE_PACKAGE_ROOT_INVALID")
    return children[0]


def apply_update(*, package: Path, active: Path, acceptance_command: list[str] | None = None, acceptance_timeout_seconds: int = 60, migration_receipt: Path | None = None, _lock_held: bool = False) -> dict:
    active = active.resolve()
    package = package.resolve()
    _validate_active(active)
    parent = active.parent.resolve()
    if not _lock_held:
        with operation_lock(parent, operation="release-update"):
            return apply_update(package=package, active=active, acceptance_command=acceptance_command, acceptance_timeout_seconds=acceptance_timeout_seconds, migration_receipt=migration_receipt, _lock_held=True)
    try:
        from scripts.deployment_transaction_state import assert_no_conflicting_journals
    except ModuleNotFoundError:
        from deployment_transaction_state import assert_no_conflicting_journals
    assert_no_conflicting_journals(parent, allowed={"release_update"})
    recovery = recover_incomplete_update(active=active)
    token = uuid.uuid4().hex
    extraction_dir = Path(tempfile.mkdtemp(prefix=".release-update-extract-", dir=parent))
    candidate = parent / f"{CANDIDATE_PREFIX}{token}"
    backup = parent / f"{BACKUP_PREFIX}{token}"
    journal_path = _journal_path(parent)
    try:
        extraction = extract(package, extraction_dir)
        project_root = _single_project_root(extraction_dir)
        os.replace(project_root, candidate)
        shutil.rmtree(extraction_dir, ignore_errors=True)
        identity = verify_source_package_identity(candidate)
        if not identity.get("verified"):
            raise RuntimeError(f"UPDATE_CANDIDATE_IDENTITY_INVALID:{identity.get('problems')}")
        pre_update_hash = _tree_sha256(active)
        candidate_hash = _tree_sha256(candidate)
        try:
            from scripts.database_migration_guard import compare_release_migrations, verify_migration_receipt
        except ModuleNotFoundError:
            from database_migration_guard import compare_release_migrations, verify_migration_receipt
        migration_plan = compare_release_migrations(active, candidate)
        migration_verification = None
        if migration_plan.get("required"):
            if migration_receipt is None:
                raise RuntimeError("UPDATE_DATABASE_MIGRATION_RECEIPT_REQUIRED")
            migration_verification = verify_migration_receipt(
                Path(migration_receipt),
                active_tree_sha256=pre_update_hash, candidate_tree_sha256=candidate_hash,
                from_head=migration_plan["from_head"], to_head=migration_plan["to_head"],
                candidate_git_commit_sha=identity.get("git_commit_sha"),
            )
        elif migration_receipt is not None:
            raise RuntimeError("UPDATE_DATABASE_MIGRATION_RECEIPT_UNEXPECTED")
        journal = {
            "schema_version": "1.0",
            "classification": "RELEASE_UPDATE_TRANSACTION",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "status": "PREPARED",
            "active_name": active.name,
            "candidate": candidate.name,
            "backup": backup.name,
            "policy": "ROLL_BACK_TO_PRE_UPDATE_TREE_IF_JOURNAL_SURVIVES",
        }
        _atomic_json(journal_path, journal)
        os.replace(active, backup)
        _atomic_json(journal_path, {**journal, "status": "ACTIVE_MOVED_TO_BACKUP"})
        os.replace(candidate, active)
        _atomic_json(journal_path, {**journal, "status": "CANDIDATE_PROMOTED"})
        final_identity = verify_source_package_identity(active)
        if not final_identity.get("verified"):
            raise RuntimeError("UPDATE_POST_CUTOVER_IDENTITY_INVALID")
        acceptance = run_post_cutover_acceptance(active, command=acceptance_command, timeout_seconds=acceptance_timeout_seconds)
        if not acceptance.get("accepted"):
            raise RuntimeError(f"UPDATE_POST_CUTOVER_ACCEPTANCE_FAILED:{acceptance.get('problems')}")
        binding = acceptance["binding"]
        acceptance_receipt = _write_acceptance_receipt(
            parent=parent, token=token, pre_tree_sha256=pre_update_hash, post_tree_sha256=_tree_sha256(active),
            post_identity=final_identity, binding=binding, migration_receipt_verification=migration_verification,
        )
        receipt = _write_rollback_receipt(backup=backup, pre_hash=pre_update_hash, post_identity=final_identity, binding=binding, acceptance_receipt=acceptance_receipt)
        try:
            from scripts.deployment_audit_chain import append_event
        except ModuleNotFoundError:
            from deployment_audit_chain import append_event
        audit_event = append_event(parent, event_type="RELEASE_UPDATE_ACCEPTED", subjects={
            "acceptance_receipt": acceptance_receipt.name,
            "acceptance_receipt_sha256": _sha256_file(acceptance_receipt),
            "rollback_receipt": receipt.name,
            "rollback_receipt_sha256": _sha256_file(receipt),
            "post_update_tree_sha256": _tree_sha256(active),
        })
        journal_path.unlink()
        return {
            "classification": "TRANSACTIONAL_RELEASE_UPDATE",
            "updated": True,
            "recovery": recovery,
            "rollback_directory": str(backup),
            "source_identity_verified": True,
            "runtime_binding": binding,
            "post_cutover_acceptance": acceptance,
            "rollback_receipt": str(receipt),
            "acceptance_receipt": str(acceptance_receipt),
            "migration_plan": migration_plan,
            "migration_receipt_verification": migration_verification,
            "deployment_audit_event_sha256": audit_event["event_sha256"],
            "policy": "POST_CUTOVER_BINDING_ACCEPTED_AND_HASH_BOUND_ROLLBACK_RETAINED_AND_AUDITED",
        }
    except BaseException:
        # If a journal exists, use the same deterministic recovery path.  If it
        # does not yet exist, active has not been swapped and staging can vanish.
        if journal_path.exists() or journal_path.is_symlink():
            try:
                recover_incomplete_update(active=active)
            except Exception:
                # Preserve authoritative recovery material for next invocation.
                raise
        raise
    finally:
        shutil.rmtree(extraction_dir, ignore_errors=True)
        if candidate.exists() and not journal_path.exists():
            shutil.rmtree(candidate, ignore_errors=True)





def _write_rollback_acceptance_receipt(*, parent: Path, rollback_payload: dict, database_compatibility: dict, rollback_acceptance: dict | None, active_tree_sha256: str) -> Path:
    token = uuid.uuid4().hex
    path = parent / f"{ROLLBACK_ACCEPTANCE_PREFIX}{token}.json"
    body = {
        "schema_version": "1.0",
        "classification": "VERIFIED_RELEASE_ROLLBACK_ACCEPTANCE_RECEIPT",
        "source_update_acceptance_receipt_sha256": rollback_payload.get("acceptance_receipt_sha256"),
        "source_rollback_receipt_sha256": _sha256_file(_receipt_path(parent / rollback_payload["backup"])),
        "active_tree_sha256": active_tree_sha256,
        "database_compatibility": database_compatibility,
        "runtime_acceptance": rollback_acceptance,
        "accepted_at": datetime.now(timezone.utc).isoformat(),
        "policy": "ROLLBACK_ACCEPTED_ONLY_AFTER_TREE_INTEGRITY_DB_COMPATIBILITY_AND_OPTIONAL_RUNTIME_ACCEPTANCE",
    }
    body["provenance_sha256"] = _canonical_hash(body)
    _atomic_json(path, body)
    return path

def _verify_rollback_database_compatibility(*, active: Path, rollback_dir: Path, rollback_payload: dict, database_probe_command: list[str] | None, timeout_seconds: int = 60) -> dict:
    acceptance_name = rollback_payload.get("acceptance_receipt")
    acceptance = _verify_acceptance_receipt(active.parent / acceptance_name) if isinstance(acceptance_name, str) else {}
    migration_receipt_sha256 = acceptance.get("migration_receipt_sha256")
    if not migration_receipt_sha256:
        return {"required": False, "compatible": True, "database_head": None, "rollback_code_head": None, "active_code_head": None, "status": "NO_DATABASE_MIGRATION_BOUND_TO_UPDATE"}
    old_head = _alembic_head(rollback_dir)
    new_head = _alembic_head(active)
    if database_probe_command is None:
        raise RuntimeError("ROLLBACK_DATABASE_COMPATIBILITY_PROBE_REQUIRED")
    try:
        from scripts.database_migration_guard import compare_release_migrations, probe_database_head
    except ModuleNotFoundError:
        from database_migration_guard import compare_release_migrations, probe_database_head
    observed = probe_database_head(database_probe_command, cwd=active, timeout_seconds=timeout_seconds)
    if observed == old_head:
        return {"required": True, "compatible": True, "database_head": observed, "rollback_code_head": old_head, "active_code_head": new_head, "status": "DATABASE_ALREADY_AT_ROLLBACK_HEAD"}
    if observed != new_head:
        raise RuntimeError(f"ROLLBACK_DATABASE_HEAD_AMBIGUOUS:{observed}:{old_head}:{new_head}")
    plan = compare_release_migrations(rollback_dir, active)
    if not plan.get("previous_release_compatible"):
        raise RuntimeError("ROLLBACK_DATABASE_SCHEMA_NOT_PREVIOUS_RELEASE_COMPATIBLE")
    return {"required": True, "compatible": True, "database_head": observed, "rollback_code_head": old_head, "active_code_head": new_head, "status": "NEW_SCHEMA_VERIFIED_COMPATIBLE_WITH_ROLLBACK_CODE", "migration_plan": plan}

def rollback_last_update(*, active: Path, rollback_dir: Path, database_probe_command: list[str] | None = None, database_probe_timeout_seconds: int = 60, rollback_acceptance_command: list[str] | None = None, rollback_acceptance_timeout_seconds: int = 60, _lock_held: bool = False) -> dict:
    active = active.resolve()
    rollback_dir = rollback_dir.resolve()
    _validate_active(active)
    parent = active.parent.resolve()
    if not _lock_held:
        with operation_lock(parent, operation="release-rollback"):
            return rollback_last_update(active=active, rollback_dir=rollback_dir, database_probe_command=database_probe_command, database_probe_timeout_seconds=database_probe_timeout_seconds, rollback_acceptance_command=rollback_acceptance_command, rollback_acceptance_timeout_seconds=rollback_acceptance_timeout_seconds, _lock_held=True)
    try:
        from scripts.deployment_transaction_state import assert_no_conflicting_journals
    except ModuleNotFoundError:
        from deployment_transaction_state import assert_no_conflicting_journals
    assert_no_conflicting_journals(parent, allowed={"release_update"})
    if rollback_dir.parent != parent or not rollback_dir.name.startswith(BACKUP_PREFIX):
        raise RuntimeError("ROLLBACK_DIRECTORY_INVALID")
    if rollback_dir.is_symlink() or not rollback_dir.is_dir():
        raise RuntimeError("ROLLBACK_DIRECTORY_UNSAFE")
    rollback_payload = _verify_rollback_receipt(rollback_dir)
    database_compatibility = _verify_rollback_database_compatibility(active=active, rollback_dir=rollback_dir, rollback_payload=rollback_payload, database_probe_command=database_probe_command, timeout_seconds=database_probe_timeout_seconds)
    if _journal_path(parent).exists() or _journal_path(parent).is_symlink():
        recover_incomplete_update(active=active)
        raise RuntimeError("ROLLBACK_RETRY_REQUIRED_AFTER_RECOVERY")
    failed = parent / f"{FAILED_PREFIX}{uuid.uuid4().hex}"
    os.replace(active, failed)
    try:
        os.replace(rollback_dir, active)
    except BaseException:
        os.replace(failed, active)
        raise
    rollback_acceptance = None
    if rollback_acceptance_command is not None:
        rollback_acceptance = run_post_cutover_acceptance(
            active, command=rollback_acceptance_command, timeout_seconds=rollback_acceptance_timeout_seconds
        )
        if not rollback_acceptance.get("accepted"):
            # Revert the rollback itself. Preserve both the verified rollback tree
            # and its receipts so an operator can inspect/retry safely.
            os.replace(active, rollback_dir)
            os.replace(failed, active)
            _validate_active(active)
            raise RuntimeError(f"ROLLBACK_POST_CUTOVER_ACCEPTANCE_FAILED:{rollback_acceptance.get('problems')}")
    _validate_active(active)
    rollback_acceptance_receipt = _write_rollback_acceptance_receipt(
        parent=parent, rollback_payload=rollback_payload, database_compatibility=database_compatibility,
        rollback_acceptance=rollback_acceptance, active_tree_sha256=_tree_sha256(active),
    )
    try:
        from scripts.deployment_audit_chain import append_event
    except ModuleNotFoundError:
        from deployment_audit_chain import append_event
    audit_event = append_event(parent, event_type="RELEASE_ROLLBACK_ACCEPTED", subjects={
        "rollback_acceptance_receipt": rollback_acceptance_receipt.name,
        "rollback_acceptance_receipt_sha256": _sha256_file(rollback_acceptance_receipt),
        "active_tree_sha256": _tree_sha256(active),
    })
    shutil.rmtree(failed, ignore_errors=True)
    _receipt_path(active.parent / rollback_dir.name).unlink(missing_ok=True)
    acceptance_name = rollback_payload.get("acceptance_receipt")
    if isinstance(acceptance_name, str):
        (parent / acceptance_name).unlink(missing_ok=True)
    return {
        "classification": "TRANSACTIONAL_RELEASE_ROLLBACK", "rolled_back": True,
        "rollback_integrity_verified": True, "database_compatibility": database_compatibility,
        "post_rollback_acceptance": rollback_acceptance,
        "rollback_acceptance_receipt": str(rollback_acceptance_receipt),
        "deployment_audit_event_sha256": audit_event["event_sha256"],
        "policy": "ROLLBACK_COMMITTED_ONLY_AFTER_OPTIONAL_RUNTIME_ACCEPTANCE; ACCEPTED_ROLLBACK_EMITS_HASH_BOUND_RECEIPT_AND_TAMPER_EVIDENT_AUDIT_EVENT",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify, stage and atomically cut over a source release with crash recovery.")
    parser.add_argument("--active", type=Path, required=True)
    parser.add_argument("--acceptance-command-json", help="JSON argv array executed after cutover without a shell; failure triggers rollback")
    parser.add_argument("--acceptance-timeout-seconds", type=int, default=60)
    parser.add_argument("--migration-receipt", type=Path, help="Verified guarded database migration receipt required when candidate Alembic head changes")
    parser.add_argument("--rollback-db-probe-command-json", help="JSON argv array used to prove DB/code compatibility before rollback after a migrated update")
    parser.add_argument("--rollback-db-probe-timeout-seconds", type=int, default=60)
    parser.add_argument("--rollback-acceptance-command-json", help="JSON argv array executed after rollback cutover; failure restores the pre-rollback active release")
    parser.add_argument("--rollback-acceptance-timeout-seconds", type=int, default=60)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--package", type=Path)
    group.add_argument("--recover-only", action="store_true")
    group.add_argument("--rollback", type=Path)
    args = parser.parse_args()
    if args.recover_only:
        result = recover_incomplete_update(active=args.active)
    elif args.rollback is not None:
        db_probe = json.loads(args.rollback_db_probe_command_json) if args.rollback_db_probe_command_json else None
        rollback_acceptance = json.loads(args.rollback_acceptance_command_json) if args.rollback_acceptance_command_json else None
        result = rollback_last_update(active=args.active, rollback_dir=args.rollback, database_probe_command=db_probe, database_probe_timeout_seconds=args.rollback_db_probe_timeout_seconds, rollback_acceptance_command=rollback_acceptance, rollback_acceptance_timeout_seconds=args.rollback_acceptance_timeout_seconds)
    else:
        command = None
        if args.acceptance_command_json:
            try:
                command = json.loads(args.acceptance_command_json)
            except json.JSONDecodeError as exc:
                raise SystemExit(f"UPDATE_ACCEPTANCE_COMMAND_JSON_INVALID:{exc}")
        result = apply_update(package=args.package, active=args.active, acceptance_command=command, acceptance_timeout_seconds=args.acceptance_timeout_seconds, migration_receipt=args.migration_receipt)
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
