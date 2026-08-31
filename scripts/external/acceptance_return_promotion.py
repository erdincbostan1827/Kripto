from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from scripts.external.acceptance_return_bundle import MANIFEST, _git_sha, _safe_rel, _secret_hits

ROOT = Path(__file__).resolve().parents[2]
CANONICAL_PREFIX = "reports/external_acceptance/"
LOCKS = ("uv.lock", "frontend/package-lock.json")
LOCK_PROMOTION_MANIFEST = "reports/lock-promotion/LOCK_PROMOTION_MANIFEST.json"
PROMOTION_CLASSIFICATION = "EXTERNAL_ACCEPTANCE_RETURN_PROMOTION_TRANSACTION"
IMPORT_LEDGER = Path("reports/acceptance_import/IMPORT_LEDGER.json")
IMPORT_LEDGER_CLASSIFICATION = "EXTERNAL_ACCEPTANCE_IMPORT_REPLAY_LEDGER"
TRANSACTION_JOURNAL = Path("reports/acceptance_import/TRANSACTION_JOURNAL.json")
TRANSACTION_JOURNAL_CLASSIFICATION = "EXTERNAL_ACCEPTANCE_IMPORT_CRASH_RECOVERY_JOURNAL"
ZERO_HASH = "0" * 64


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_staged(staged: Path, *, root: Path) -> tuple[dict[str, Any], list[str]]:
    problems: list[str] = []
    marker = staged / MANIFEST
    try:
        manifest = json.loads(marker.read_text(encoding="utf-8"))
    except Exception as exc:
        return {}, [f"STAGED_MANIFEST_INVALID:{type(exc).__name__}"]
    local_git = _git_sha(root)
    if not local_git:
        problems.append("LOCAL_GIT_UNAVAILABLE")
    if manifest.get("source_git_commit_sha") != local_git:
        problems.append("SOURCE_GIT_MISMATCH")
    rows = manifest.get("files") if isinstance(manifest.get("files"), list) else []
    if manifest.get("file_count") != len(rows):
        problems.append("FILE_COUNT_MISMATCH")
    seen: set[str] = set()
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get("path"), str):
            problems.append("STAGED_ENTRY_INVALID"); continue
        rel = row["path"]
        if not _safe_rel(rel):
            problems.append(f"STAGED_PATH_UNSAFE:{rel}"); continue
        if rel in seen:
            problems.append(f"STAGED_DUPLICATE:{rel}")
        seen.add(rel)
        p = staged / rel
        current = staged
        for part in Path(rel).parts:
            current = current / part
            if current.is_symlink():
                problems.append(f"STAGED_SYMLINK_NOT_ALLOWED:{rel}")
        if not p.is_file():
            problems.append(f"STAGED_FILE_MISSING:{rel}"); continue
        data = p.read_bytes()
        if hashlib.sha256(data).hexdigest() != row.get("sha256"):
            problems.append(f"STAGED_HASH_MISMATCH:{rel}")
        if len(data) != row.get("size"):
            problems.append(f"STAGED_SIZE_MISMATCH:{rel}")
        for hit in _secret_hits(data):
            problems.append(f"{hit}:{rel}")
    return manifest, sorted(set(problems))



def _artifact_classes(paths: list[str]) -> list[str]:
    classes: set[str] = set()
    for rel in paths:
        if rel in LOCKS or rel == LOCK_PROMOTION_MANIFEST:
            classes.add("DEPENDENCY_LOCK_CANDIDATE")
        if rel == "reports/CI_BUILD_EVIDENCE_MANIFEST.json":
            classes.add("CI_BUILD_EVIDENCE")
        if rel.startswith(CANONICAL_PREFIX):
            classes.add("CANONICAL_EXTERNAL_ACCEPTANCE")
        if rel.endswith("manifest_frontend.json") or "browser" in rel.lower() or "frontend" in rel.lower():
            classes.add("FRONTEND_BROWSER_EVIDENCE")
        if any(token in rel for token in ("sbom", "dependency_licenses", "supply_chain", "scanner_image", "provenance")):
            classes.add("SUPPLY_CHAIN_EVIDENCE")
        if any(token in rel for token in ("release_challenge", "evidence_ledger", "ledger_checkpoint")):
            classes.add("TRUST_CHAIN_EVIDENCE")
    return sorted(classes)


def _ledger_event_hash(event: dict[str, Any]) -> str:
    payload = {k: v for k, v in event.items() if k != "event_hash"}
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _load_import_ledger(root: Path) -> tuple[dict[str, Any], list[str]]:
    path = root / IMPORT_LEDGER
    if not path.exists():
        return {"schema_version": "1.0", "classification": IMPORT_LEDGER_CLASSIFICATION, "events": []}, []
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {}, [f"IMPORT_LEDGER_INVALID:{type(exc).__name__}"]
    problems: list[str] = []
    if doc.get("schema_version") != "1.0": problems.append("IMPORT_LEDGER_SCHEMA_INVALID")
    if doc.get("classification") != IMPORT_LEDGER_CLASSIFICATION: problems.append("IMPORT_LEDGER_CLASSIFICATION_INVALID")
    events = doc.get("events") if isinstance(doc.get("events"), list) else []
    if doc.get("events") is not events: problems.append("IMPORT_LEDGER_EVENTS_INVALID")
    previous = ZERO_HASH
    seen: set[str] = set()
    for index, event in enumerate(events):
        if not isinstance(event, dict):
            problems.append(f"IMPORT_LEDGER_EVENT_INVALID:{index}"); continue
        if event.get("previous_event_hash") != previous:
            problems.append(f"IMPORT_LEDGER_CHAIN_INVALID:{index}")
        expected = _ledger_event_hash(event)
        if event.get("event_hash") != expected:
            problems.append(f"IMPORT_LEDGER_HASH_INVALID:{index}")
        bundle = event.get("bundle_manifest_sha256")
        if not isinstance(bundle, str) or len(bundle) != 64:
            problems.append(f"IMPORT_LEDGER_BUNDLE_INVALID:{index}")
        elif bundle in seen:
            problems.append(f"IMPORT_LEDGER_DUPLICATE_BUNDLE:{index}")
        else:
            seen.add(bundle)
        previous = event.get("event_hash") if isinstance(event.get("event_hash"), str) else ZERO_HASH
    return doc, sorted(set(problems))


def _atomic_json(path: Path, payload: dict[str, Any], *, mode: int = 0o600) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.parent / f".{path.name}.tmp-{os.getpid()}"
    temp.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.chmod(temp, mode)
    os.replace(temp, path)


def _trust_anchor_from_staged(staged: Path) -> dict[str, Any]:
    """Capture immutable hashes/head claims; semantic verification remains authoritative."""
    anchor: dict[str, Any] = {}
    ledger_path = staged / "reports/external_acceptance/evidence_ledger.json"
    if ledger_path.is_file():
        anchor["external_evidence_ledger_sha256"] = _sha(ledger_path)
        try:
            from backend.app.release.evidence_ledger import verify_ledger
            verified = verify_ledger(ledger_path)
            anchor["external_evidence_ledger_verified"] = verified.get("verified") is True
            anchor["external_evidence_ledger_head_hash"] = verified.get("head_hash")
            anchor["external_evidence_ledger_entries"] = verified.get("entries")
        except Exception as exc:
            anchor["external_evidence_ledger_verified"] = False
            anchor["external_evidence_ledger_error"] = type(exc).__name__
    checkpoint = staged / "reports/external_acceptance/evidence_ledger_checkpoint.json"
    if checkpoint.is_file():
        anchor["ledger_checkpoint_sha256"] = _sha(checkpoint)
        try:
            doc = json.loads(checkpoint.read_text(encoding="utf-8"))
            anchor["ledger_checkpoint_head_hash"] = doc.get("ledger_head_hash")
            anchor["ledger_checkpoint_signature_sha256"] = doc.get("signature_sha256")
            anchor["ledger_checkpoint_signer_key_id"] = doc.get("signer_key_id")
        except Exception:
            anchor["ledger_checkpoint_parse_error"] = True
    challenge = staged / "reports/external_acceptance/release_challenge.json"
    if challenge.is_file():
        anchor["release_challenge_sha256"] = _sha(challenge)
    return anchor


def _write_transaction_journal(root: Path, payload: dict[str, Any]) -> str:
    doc = {
        "schema_version": "1.0",
        "classification": TRANSACTION_JOURNAL_CLASSIFICATION,
        **payload,
        "updated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }
    _atomic_json(root / TRANSACTION_JOURNAL, doc)
    return str(root / TRANSACTION_JOURNAL)


def _ledger_contains_bundle(root: Path, bundle_sha: str) -> bool:
    doc, problems = _load_import_ledger(root)
    if problems:
        return False
    return any(isinstance(e, dict) and e.get("bundle_manifest_sha256") == bundle_sha for e in doc.get("events", []))


def recover_pending_transaction(root: Path = ROOT) -> dict[str, Any]:
    """Recover an interrupted canonical swap deterministically before another promotion."""
    root = root.resolve()
    journal_path = root / TRANSACTION_JOURNAL
    if not journal_path.is_file():
        return {"recovered": False, "status": "NO_PENDING_TRANSACTION", "problems": []}
    try:
        doc = json.loads(journal_path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"recovered": False, "status": "JOURNAL_INVALID", "problems": [f"TRANSACTION_JOURNAL_INVALID:{type(exc).__name__}"]}
    problems: list[str] = []
    if doc.get("schema_version") != "1.0" or doc.get("classification") != TRANSACTION_JOURNAL_CLASSIFICATION:
        return {"recovered": False, "status": "JOURNAL_INVALID", "problems": ["TRANSACTION_JOURNAL_CONTRACT_INVALID"]}
    status = doc.get("status")
    if status in {"COMMITTED", "ROLLED_BACK"}:
        journal_path.unlink(missing_ok=True)
        return {"recovered": True, "status": f"CLEANED_{status}", "problems": []}
    bundle_sha = doc.get("bundle_manifest_sha256")
    if not isinstance(bundle_sha, str) or len(bundle_sha) != 64:
        return {"recovered": False, "status": "JOURNAL_INVALID", "problems": ["TRANSACTION_JOURNAL_BUNDLE_INVALID"]}
    canonical = root / "reports/external_acceptance"
    backup = root / str(doc.get("backup_relpath", ""))
    replacement = root / str(doc.get("replacement_relpath", ""))
    lock_candidate_rel = doc.get("lock_candidate_relpath")
    lock_candidate = root / lock_candidate_rel if isinstance(lock_candidate_rel, str) and lock_candidate_rel else None
    ledger_has = _ledger_contains_bundle(root, bundle_sha)
    if ledger_has:
        shutil.rmtree(backup, ignore_errors=True)
        shutil.rmtree(replacement, ignore_errors=True)
        _write_transaction_journal(root, {**doc, "status": "COMMITTED", "recovery_action": "FINALIZED_AFTER_LEDGER_COMMIT"})
        journal_path.unlink(missing_ok=True)
        return {"recovered": True, "status": "FINALIZED_COMMIT", "bundle_manifest_sha256": bundle_sha, "problems": []}
    # No authoritative import-ledger event exists: canonical swap must not survive.
    try:
        if canonical.exists():
            shutil.rmtree(canonical, ignore_errors=True)
        if backup.exists():
            os.replace(backup, canonical)
        shutil.rmtree(replacement, ignore_errors=True)
        if lock_candidate is not None and doc.get("lock_candidate_preexisting") is not True:
            shutil.rmtree(lock_candidate, ignore_errors=True)
        _write_transaction_journal(root, {**doc, "status": "ROLLED_BACK", "recovery_action": "ROLLBACK_NO_LEDGER_COMMIT"})
        journal_path.unlink(missing_ok=True)
        return {"recovered": True, "status": "ROLLED_BACK", "bundle_manifest_sha256": bundle_sha, "problems": []}
    except Exception as exc:
        problems.append(f"TRANSACTION_RECOVERY_FAILED:{type(exc).__name__}")
        return {"recovered": False, "status": "RECOVERY_FAILED", "bundle_manifest_sha256": bundle_sha, "problems": problems}


def _append_import_ledger(root: Path, *, bundle_manifest_sha256: str, source_git_commit_sha: str, promoted_files: list[str], artifact_classes: list[str], trust_anchor: dict[str, Any] | None = None) -> str:
    doc, problems = _load_import_ledger(root)
    if problems:
        raise ValueError(";".join(problems))
    events = list(doc.get("events", []))
    previous = events[-1]["event_hash"] if events else ZERO_HASH
    event = {
        "schema_version": "1.0",
        "source_git_commit_sha": source_git_commit_sha,
        "bundle_manifest_sha256": bundle_manifest_sha256,
        "promoted_files": sorted(promoted_files),
        "artifact_classes": sorted(artifact_classes),
        "trust_anchor": dict(sorted((trust_anchor or {}).items())),
        "recorded_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "previous_event_hash": previous,
    }
    event["event_hash"] = _ledger_event_hash(event)
    events.append(event)
    new_doc = {"schema_version": "1.0", "classification": IMPORT_LEDGER_CLASSIFICATION, "events": events}
    path = root / IMPORT_LEDGER
    _atomic_json(path, new_doc)
    return str(path)


def _post_promotion_verify(root: Path, *, max_age_hours: int) -> dict[str, Any]:
    from scripts.verify_external_acceptance import verify_manifest
    from scripts.release_gate import evaluate_release_gate
    profiles: dict[str, Any] = {}
    problems: list[str] = []
    for path in sorted((root / "reports" / "external_acceptance").glob("manifest_*.json")):
        if not path.is_file():
            continue
        result = verify_manifest(path, root=root, max_age_hours=max_age_hours)
        profiles[path.name] = result
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            doc = {}
        release_claim = doc.get("selected_all_pass") is True or any(v == "PASS" for v in (result.get("groups") or {}).values())
        if release_claim and result.get("verified") is not True:
            problems.extend(f"POST_PROMOTION_SEMANTIC_INVALID:{path.name}:{item}" for item in result.get("problems", ["UNVERIFIED"]))
    gate_blockers = evaluate_release_gate(root)
    return {"verified": not problems, "problems": sorted(set(problems)), "profiles": profiles, "release_gate_blockers": gate_blockers, "release_gate_eligible": not gate_blockers}

def _candidate_worktree(root: Path) -> tuple[Path, Path]:
    parent = Path(tempfile.mkdtemp(prefix="acceptance-promotion-assess-"))
    worktree = parent / "repo"
    subprocess.run(["git", "worktree", "add", "--detach", "-q", str(worktree), "HEAD"], cwd=root, check=True,
                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return parent, worktree


def _cleanup_worktree(root: Path, parent: Path, worktree: Path) -> None:
    try:
        subprocess.run(["git", "worktree", "remove", "--force", str(worktree)], cwd=root, check=False,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    finally:
        shutil.rmtree(parent, ignore_errors=True)


def _semantic_verify_candidate(staged: Path, *, root: Path, rows: list[dict[str, Any]], max_age_hours: int) -> dict[str, Any]:
    parent, candidate = _candidate_worktree(root)
    try:
        for row in rows:
            rel = row.get("path")
            if not isinstance(rel, str) or rel in LOCKS:
                continue
            src = staged / rel
            dest = candidate / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest)
        # Runtime reports may be needed by challenge dirty-worktree logic but source files must stay immutable.
        from scripts.verify_external_acceptance import verify_manifest
        profiles: dict[str, Any] = {}
        manifest_paths = sorted(
            p for p in (candidate / "reports" / "external_acceptance").glob("manifest_*.json") if p.is_file()
        )
        for p in manifest_paths:
            result = verify_manifest(p, root=candidate, max_age_hours=max_age_hours)
            profiles[p.name] = result
        release_relevant = {
            name: result for name, result in profiles.items()
            if any(status == "PASS" for status in (result.get("groups") or {}).values())
        }
        problems: list[str] = []
        for name, result in release_relevant.items():
            if not result.get("verified"):
                problems.extend(f"SEMANTIC_INVALID:{name}:{p}" for p in result.get("problems", []))
        # If an aggregate claims selected_all_pass, it must itself verify.
        all_result = profiles.get("manifest_all.json")
        if isinstance(all_result, dict):
            try:
                doc = json.loads((candidate / "reports/external_acceptance/manifest_all.json").read_text(encoding="utf-8"))
            except Exception:
                doc = {}
            if doc.get("selected_all_pass") is True and not all_result.get("verified"):
                problems.append("SEMANTIC_INVALID:manifest_all.json:SELECTED_ALL_PASS_NOT_VERIFIED")
        return {"verified": not problems, "problems": sorted(set(problems)), "profiles": profiles}
    finally:
        _cleanup_worktree(root, parent, candidate)


def assess(staged: Path, *, root: Path = ROOT, max_age_hours: int = 168) -> dict[str, Any]:
    staged = staged.resolve(); root = root.resolve()
    manifest, problems = _load_staged(staged, root=root)
    rows = manifest.get("files") if isinstance(manifest.get("files"), list) else []
    paths = [r.get("path") for r in rows if isinstance(r, dict) and isinstance(r.get("path"), str)]
    lock_paths = sorted(p for p in paths if p in LOCKS)
    if lock_paths and set(lock_paths) != set(LOCKS):
        problems.append("LOCK_SET_PARTIAL")
    if lock_paths and LOCK_PROMOTION_MANIFEST not in paths:
        problems.append("LOCK_PROMOTION_MANIFEST_MISSING")
    canonical = sorted(p for p in paths if p.startswith(CANONICAL_PREFIX) and "/incoming/" not in p)
    bundle_manifest_sha = _sha(staged / MANIFEST) if (staged / MANIFEST).is_file() else None
    ledger, ledger_problems = _load_import_ledger(root)
    problems.extend(ledger_problems)
    if bundle_manifest_sha and any(e.get("bundle_manifest_sha256") == bundle_manifest_sha for e in ledger.get("events", []) if isinstance(e, dict)):
        problems.append("RETURN_BUNDLE_REPLAY")
    artifact_classes = _artifact_classes(paths)
    semantic = {"verified": False, "problems": ["TRANSPORT_INVALID"], "profiles": {}}
    if not problems:
        try:
            semantic = _semantic_verify_candidate(staged, root=root, rows=rows, max_age_hours=max_age_hours)
        except Exception as exc:
            semantic = {"verified": False, "problems": [f"SEMANTIC_ASSESSMENT_ERROR:{type(exc).__name__}"], "profiles": {}}
        problems.extend(semantic.get("problems", []))
    return {
        "verified": not problems and semantic.get("verified") is True,
        "classification": PROMOTION_CLASSIFICATION,
        "source_git_commit_sha": manifest.get("source_git_commit_sha"),
        "staged_bundle_path": str(staged),
        "canonical_evidence_files": canonical,
        "lock_candidate_files": lock_paths,
        "locks_auto_promotable": False,
        "bundle_manifest_sha256": bundle_manifest_sha,
        "artifact_classes": artifact_classes,
        "import_contract_verified": not problems,
        "semantic": semantic,
        "problems": sorted(set(problems)),
    }


def _copy_lock_candidates(staged: Path, *, root: Path, bundle_sha: str, paths: list[str]) -> str | None:
    if not paths:
        return None
    target = root / "reports" / "lock-promotion" / "candidates" / bundle_sha
    if target.exists():
        return str(target)
    temp = target.parent / f".{bundle_sha}.tmp"
    shutil.rmtree(temp, ignore_errors=True)
    for rel in [*paths, LOCK_PROMOTION_MANIFEST]:
        src = staged / rel
        if src.is_file():
            dest = temp / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest)
            os.chmod(dest, 0o600)
    target.parent.mkdir(parents=True, exist_ok=True)
    os.replace(temp, target)
    return str(target)


def promote(staged: Path, *, root: Path = ROOT, confirm_source_sha: str, max_age_hours: int = 168) -> dict[str, Any]:
    root = root.resolve(); staged = staged.resolve()
    recovery = recover_pending_transaction(root)
    if recovery.get("problems"):
        return {"verified": False, "promoted": False, "classification": PROMOTION_CLASSIFICATION, "recovery": recovery, "problems": recovery["problems"]}
    assessment = assess(staged, root=root, max_age_hours=max_age_hours)
    local_git = _git_sha(root)
    if confirm_source_sha != local_git or assessment.get("source_git_commit_sha") != local_git:
        return {**assessment, "promoted": False, "problems": sorted(set(assessment["problems"] + ["PROMOTION_SOURCE_CONFIRMATION_MISMATCH"]))}
    if not assessment["verified"]:
        return {**assessment, "promoted": False}
    marker = staged / MANIFEST
    bundle_sha = assessment["bundle_manifest_sha256"]
    canonical_dir = root / "reports" / "external_acceptance"
    parent = canonical_dir.parent
    replacement = parent / f".external_acceptance.promote-{bundle_sha[:16]}"
    backup = parent / f".external_acceptance.rollback-{bundle_sha[:16]}"
    shutil.rmtree(replacement, ignore_errors=True); shutil.rmtree(backup, ignore_errors=True)
    if canonical_dir.exists():
        shutil.copytree(canonical_dir, replacement, symlinks=False)
    else:
        replacement.mkdir(parents=True)
    for rel in assessment["canonical_evidence_files"]:
        suffix = Path(rel).relative_to("reports/external_acceptance")
        dest = replacement / suffix
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(staged / rel, dest)
        os.chmod(dest, 0o600)
    transaction = {
        "schema_version": "2.0", "classification": PROMOTION_CLASSIFICATION,
        "source_git_commit_sha": local_git, "staged_manifest_sha256": bundle_sha,
        "promoted_files": assessment["canonical_evidence_files"],
        "artifact_classes": assessment["artifact_classes"],
        "truth_policy": "Promotion transports semantically verified evidence only; post-swap verification and canonical release gates remain authoritative.",
    }
    (replacement / "PROMOTION_TRANSACTION.json").write_text(json.dumps(transaction, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    had_canonical = canonical_dir.exists()
    post: dict[str, Any] = {"verified": False, "problems": ["POST_PROMOTION_NOT_RUN"]}
    lock_candidate: str | None = None
    lock_candidate_preexisting = (root / "reports" / "lock-promotion" / "candidates" / bundle_sha).exists()
    trust_anchor = _trust_anchor_from_staged(staged)
    journal_base = {
        "status": "PREPARED", "bundle_manifest_sha256": bundle_sha, "source_git_commit_sha": local_git,
        "canonical_relpath": "reports/external_acceptance",
        "replacement_relpath": replacement.relative_to(root).as_posix(),
        "backup_relpath": backup.relative_to(root).as_posix(),
        "lock_candidate_relpath": f"reports/lock-promotion/candidates/{bundle_sha}" if assessment["lock_candidate_files"] else None,
        "lock_candidate_preexisting": lock_candidate_preexisting,
        "trust_anchor": trust_anchor,
    }
    _write_transaction_journal(root, journal_base)
    try:
        if had_canonical:
            os.replace(canonical_dir, backup)
        os.replace(replacement, canonical_dir)
        _write_transaction_journal(root, {**journal_base, "status": "CANONICAL_SWAPPED"})
        post = _post_promotion_verify(root, max_age_hours=max_age_hours)
        if not post.get("verified"):
            raise RuntimeError("POST_PROMOTION_VERIFICATION_FAILED")
        lock_candidate = _copy_lock_candidates(staged, root=root, bundle_sha=bundle_sha, paths=assessment["lock_candidate_files"])
        _write_transaction_journal(root, {**journal_base, "status": "POST_VERIFIED", "lock_candidate_path": lock_candidate})
        ledger_path = _append_import_ledger(
            root, bundle_manifest_sha256=bundle_sha, source_git_commit_sha=local_git,
            promoted_files=assessment["canonical_evidence_files"], artifact_classes=assessment["artifact_classes"], trust_anchor=trust_anchor,
        )
        _write_transaction_journal(root, {**journal_base, "status": "LEDGER_COMMITTED", "import_ledger_path": ledger_path})
    except Exception as exc:
        # Roll back canonical evidence for *any* post-swap failure. The import ledger is
        # appended only after verification, so failed transactions cannot become replay-authoritative.
        if canonical_dir.exists():
            shutil.rmtree(canonical_dir, ignore_errors=True)
        if had_canonical and backup.exists():
            os.replace(backup, canonical_dir)
        shutil.rmtree(replacement, ignore_errors=True)
        if lock_candidate and not lock_candidate_preexisting:
            shutil.rmtree(Path(lock_candidate), ignore_errors=True)
        _write_transaction_journal(root, {**journal_base, "status": "ROLLED_BACK", "rollback_error": type(exc).__name__})
        (root / TRANSACTION_JOURNAL).unlink(missing_ok=True)
        problems = assessment["problems"] + post.get("problems", []) + [f"PROMOTION_TRANSACTION_ROLLED_BACK:{type(exc).__name__}"]
        return {**assessment, "promoted": False, "rolled_back": True, "post_promotion": post, "recovery": recovery, "problems": sorted(set(problems))}
    else:
        shutil.rmtree(backup, ignore_errors=True)
        _write_transaction_journal(root, {**journal_base, "status": "COMMITTED", "import_ledger_path": ledger_path})
        (root / TRANSACTION_JOURNAL).unlink(missing_ok=True)
    return {**assessment, "promoted": True, "rolled_back": False, "post_promotion": post, "recovery": recovery, "trust_anchor": trust_anchor, "promotion_transaction": str(canonical_dir / "PROMOTION_TRANSACTION.json"), "import_ledger_path": ledger_path, "lock_candidate_path": lock_candidate}


def main() -> int:
    p = argparse.ArgumentParser(description="Assess or atomically promote a staged external acceptance return bundle")
    sub = p.add_subparsers(dest="command", required=True)
    a = sub.add_parser("assess"); a.add_argument("staged", type=Path); a.add_argument("--max-age-hours", type=int, default=168)
    pr = sub.add_parser("promote"); pr.add_argument("staged", type=Path); pr.add_argument("--confirm-source-sha", required=True); pr.add_argument("--max-age-hours", type=int, default=168)
    args = p.parse_args()
    result = assess(args.staged, max_age_hours=max(1, args.max_age_hours)) if args.command == "assess" else promote(args.staged, confirm_source_sha=args.confirm_source_sha, max_age_hours=max(1, args.max_age_hours))
    print(json.dumps(result, indent=2, sort_keys=True, default=str))
    return 0 if result.get("verified") and (args.command != "promote" or result.get("promoted")) else 2


if __name__ == "__main__":
    raise SystemExit(main())
