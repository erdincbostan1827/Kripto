from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
import json
import os
import tempfile
from typing import Any

fcntl: Any
try:
    import fcntl as _fcntl
    fcntl = _fcntl
except ImportError:  # pragma: no cover - production acceptance is Linux
    fcntl = None

GENESIS = "0" * 64


def _path_has_symlink_component(path: Path, *, root: Path) -> bool:
    root_abs = root.absolute()
    path_abs = path.absolute()
    try:
        rel = path_abs.relative_to(root_abs)
    except ValueError as exc:
        raise ValueError("ledger path escapes configured root") from exc
    current = root_abs
    for part in rel.parts:
        current = current / part
        if current.is_symlink():
            return True
    return False


def canonical_hash(payload: dict[str, Any]) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return sha256(raw).hexdigest()


def _atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2, sort_keys=True)
            fh.write("\n")
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(temp_name, path)
        try:
            dir_fd = os.open(path.parent, os.O_RDONLY)
            try:
                os.fsync(dir_fd)
            finally:
                os.close(dir_fd)
        except OSError as exc:
            _ = exc  # Directory fsync is best-effort on filesystems that do not support it.
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def append_entry(path: Path, *, manifest_sha256: str, challenge_id: str, git_commit_sha: str, profile: str, root: Path | None = None) -> dict[str, Any]:
    raw_path = path
    if root is not None:
        if _path_has_symlink_component(raw_path, root=root):
            raise ValueError("ledger path contains symlink component")
    elif raw_path.is_symlink():
        raise ValueError("ledger path must not be a symlink")
    path = raw_path.resolve()
    if root is not None:
        root_resolved = root.resolve()
        try:
            path.relative_to(root_resolved)
        except ValueError as exc:
            raise ValueError("ledger path escapes configured root") from exc
    path.parent.mkdir(parents=True, exist_ok=True)
    lock_path = path.with_suffix(path.suffix + ".lock")
    with lock_path.open("a+", encoding="utf-8") as lock_fh:
        if fcntl is not None:
            fcntl.flock(lock_fh.fileno(), fcntl.LOCK_EX)
        try:
            entries: list[dict[str, Any]] = []
            if path.is_file():
                verified = verify_ledger(path)
                if not verified.get("verified"):
                    raise ValueError("refusing to append to invalid evidence ledger: " + ",".join(verified.get("problems") or []))
                doc = json.loads(path.read_text(encoding="utf-8"))
                entries = list(doc.get("entries") or [])
            prev = entries[-1]["entry_hash"] if entries else GENESIS
            core = {
                "sequence": len(entries) + 1,
                "observed_at": datetime.now(timezone.utc).isoformat(),
                "manifest_sha256": manifest_sha256,
                "challenge_id": challenge_id,
                "git_commit_sha": git_commit_sha,
                "profile": profile,
                "previous_hash": prev,
            }
            entry = {**core, "entry_hash": canonical_hash(core)}
            entries.append(entry)
            payload = {
                "schema_version": "1.0",
                "classification": "EXTERNAL_ACCEPTANCE_APPEND_ONLY_EVIDENCE_LEDGER",
                "entries": entries,
            }
            _atomic_write_json(path, payload)
            return entry
        finally:
            if fcntl is not None:
                fcntl.flock(lock_fh.fileno(), fcntl.LOCK_UN)


def verify_ledger(path: Path) -> dict[str, Any]:
    if path.is_symlink():
        return {"verified": False, "problems": ["LEDGER_SYMLINK_NOT_ALLOWED"], "entries": 0}
    if not path.is_file():
        return {"verified": False, "problems": ["LEDGER_MISSING"], "entries": 0}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"verified": False, "problems": [f"LEDGER_INVALID_JSON:{type(exc).__name__}"], "entries": 0}
    problems: list[str] = []
    if payload.get("schema_version") != "1.0":
        problems.append("LEDGER_SCHEMA_VERSION_INVALID")
    if payload.get("classification") != "EXTERNAL_ACCEPTANCE_APPEND_ONLY_EVIDENCE_LEDGER":
        problems.append("LEDGER_INVALID_CLASSIFICATION")
    entries = payload.get("entries")
    if not isinstance(entries, list):
        return {"verified": False, "problems": problems + ["LEDGER_ENTRIES_NOT_LIST"], "entries": 0}
    prev = GENESIS
    seen_manifest: set[str] = set()
    for idx, entry in enumerate(entries, start=1):
        if not isinstance(entry, dict):
            problems.append(f"LEDGER_ENTRY_INVALID:{idx}")
            continue
        if entry.get("sequence") != idx:
            problems.append(f"LEDGER_SEQUENCE_INVALID:{idx}")
        if entry.get("previous_hash") != prev:
            problems.append(f"LEDGER_PREVIOUS_HASH_MISMATCH:{idx}")
        core = {k: entry.get(k) for k in ("sequence", "observed_at", "manifest_sha256", "challenge_id", "git_commit_sha", "profile", "previous_hash")}
        expected = canonical_hash(core)
        if entry.get("entry_hash") != expected:
            problems.append(f"LEDGER_ENTRY_HASH_MISMATCH:{idx}")
        mh = entry.get("manifest_sha256")
        if mh in seen_manifest:
            problems.append(f"LEDGER_MANIFEST_REPLAY:{idx}")
        if isinstance(mh, str):
            seen_manifest.add(mh)
        prev = str(entry.get("entry_hash") or prev)
    return {"verified": not problems, "problems": problems, "entries": len(entries), "head_hash": prev}
