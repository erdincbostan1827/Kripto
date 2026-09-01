from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
import json
import os
from scripts.bounded_subprocess import run_captured
from typing import Any

from backend.app.release.acceptance_challenge import verify_challenge
from backend.app.release.evidence_ledger import verify_ledger

SCHEMA_VERSION = "1.0"
CLASSIFICATION = "REAL_EXTERNAL_ACCEPTANCE_SIGNED_LEDGER_CHECKPOINT"
DEFAULT_PATH = Path("reports/external_acceptance/evidence_ledger_checkpoint.json")
LEDGER_PATH = Path("reports/external_acceptance/evidence_ledger.json")


def _path_has_symlink_component(path: Path, *, root: Path) -> bool:
    root_abs = root.absolute()
    path_abs = path.absolute()
    try:
        rel = path_abs.relative_to(root_abs)
    except ValueError as exc:
        raise ValueError("path escapes configured root") from exc
    current = root_abs
    for part in rel.parts:
        current = current / part
        if current.is_symlink():
            return True
    return False


def _sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _time(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def verify_ledger_checkpoint(
    path: Path,
    *,
    root: Path,
    max_age_hours: int = 24,
    expected_environment: dict[str, Any] | None = None,
    require_external_trust: bool = True,
) -> dict[str, Any]:
    problems: list[str] = []
    raw_root = root
    raw_path = path
    try:
        if _path_has_symlink_component(raw_path, root=raw_root):
            return {"verified": False, "problems": ["LEDGER_CHECKPOINT_SYMLINK_NOT_ALLOWED"]}
    except ValueError:
        return {"verified": False, "problems": ["LEDGER_CHECKPOINT_PATH_ESCAPE"]}
    root = raw_root.resolve()
    path = raw_path.resolve()
    try:
        path.relative_to(root)
    except ValueError:
        return {"verified": False, "problems": ["LEDGER_CHECKPOINT_PATH_ESCAPE"]}
    if not path.is_file():
        return {"verified": False, "problems": ["LEDGER_CHECKPOINT_MISSING"]}
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"verified": False, "problems": [f"LEDGER_CHECKPOINT_INVALID_JSON:{type(exc).__name__}"]}

    if doc.get("schema_version") != SCHEMA_VERSION:
        problems.append("LEDGER_CHECKPOINT_SCHEMA_INVALID")
    if doc.get("classification") != CLASSIFICATION:
        problems.append("LEDGER_CHECKPOINT_CLASSIFICATION_INVALID")
    if doc.get("real_system") is not True or doc.get("executed") is not True:
        problems.append("LEDGER_CHECKPOINT_NOT_REAL_EXECUTION")
    if doc.get("signature_verified") is not True:
        problems.append("LEDGER_CHECKPOINT_SIGNATURE_NOT_VERIFIED")
    for key in ("signer_identity", "signer_key_id", "signature_mechanism"):
        if not isinstance(doc.get(key), str) or not doc[key].strip():
            problems.append(f"LEDGER_CHECKPOINT_FIELD_MISSING:{key}")

    observed = _time(doc.get("observed_at"))
    if observed is None:
        problems.append("LEDGER_CHECKPOINT_OBSERVED_AT_INVALID")
    else:
        age = (datetime.now(timezone.utc) - observed.astimezone(timezone.utc)).total_seconds() / 3600
        if age < -1 or age > max_age_hours:
            problems.append("LEDGER_CHECKPOINT_STALE")

    raw_ledger_path = root / LEDGER_PATH
    if _path_has_symlink_component(raw_ledger_path, root=root):
        problems.append("LEDGER_CHECKPOINT_LEDGER_SYMLINK_NOT_ALLOWED")
        ledger_path = raw_ledger_path.resolve()
        ledger = {"verified": False, "problems": ["LEDGER_SYMLINK_NOT_ALLOWED"], "entries": 0, "head_hash": None}
    else:
        ledger_path = raw_ledger_path.resolve()
        ledger = verify_ledger(ledger_path)
    if not ledger.get("verified"):
        problems.append("LEDGER_CHECKPOINT_LEDGER_INVALID")
    else:
        if doc.get("ledger_sha256") != _sha(ledger_path):
            problems.append("LEDGER_CHECKPOINT_LEDGER_HASH_MISMATCH")
        if doc.get("ledger_head_hash") != ledger.get("head_hash"):
            problems.append("LEDGER_CHECKPOINT_HEAD_HASH_MISMATCH")
        if doc.get("ledger_entries") != ledger.get("entries"):
            problems.append("LEDGER_CHECKPOINT_ENTRY_COUNT_MISMATCH")
    if doc.get("ledger_artifact") != LEDGER_PATH.as_posix():
        problems.append("LEDGER_CHECKPOINT_LEDGER_TARGET_INVALID")

    challenge = verify_challenge(
        root / "reports/external_acceptance/release_challenge.json", root=root, require_trust=True
    )
    bound = doc.get("release_challenge") if isinstance(doc.get("release_challenge"), dict) else {}
    if not challenge.get("verified"):
        problems.append("LEDGER_CHECKPOINT_CHALLENGE_NOT_VERIFIED")
    elif bound.get("challenge_id") != challenge.get("challenge_id") or bound.get("sha256") != challenge.get("sha256"):
        problems.append("LEDGER_CHECKPOINT_CHALLENGE_MISMATCH")

    try:
        git_proc = run_captured(["git", "rev-parse", "HEAD"], cwd=root, timeout=10)
        current_git = git_proc.stdout.strip() if git_proc.returncode == 0 else None
        if not current_git:
            problems.append("LEDGER_CHECKPOINT_GIT_UNAVAILABLE")
    except Exception:
        current_git = None
        problems.append("LEDGER_CHECKPOINT_GIT_UNAVAILABLE")
    if current_git and doc.get("git_commit_sha") != current_git:
        problems.append("LEDGER_CHECKPOINT_GIT_MISMATCH")

    expected = expected_environment if isinstance(expected_environment, dict) else {}
    expected_env = expected.get("acceptance_environment_id_hash")
    expected_topology = expected.get("topology_hash")
    environment = doc.get("environment") if isinstance(doc.get("environment"), dict) else {}
    if not isinstance(expected_env, str) or len(expected_env) != 64:
        problems.append("LEDGER_CHECKPOINT_EXPECTED_ENVIRONMENT_MISSING")
    elif environment.get("acceptance_environment_id_hash") != expected_env:
        problems.append("LEDGER_CHECKPOINT_ENVIRONMENT_MISMATCH")
    if not isinstance(expected_topology, str) or len(expected_topology) != 64:
        problems.append("LEDGER_CHECKPOINT_EXPECTED_TOPOLOGY_MISSING")
    elif environment.get("topology_hash") != expected_topology:
        problems.append("LEDGER_CHECKPOINT_TOPOLOGY_MISMATCH")

    sig_rel = doc.get("signature_artifact")
    sig_hash = doc.get("signature_sha256")
    sig_path: Path | None = None
    if not isinstance(sig_rel, str) or not sig_rel or not isinstance(sig_hash, str) or len(sig_hash) != 64:
        problems.append("LEDGER_CHECKPOINT_SIGNATURE_BINDING_INVALID")
    else:
        raw_sig_path = root / sig_rel
        try:
            if _path_has_symlink_component(raw_sig_path, root=root):
                problems.append("LEDGER_CHECKPOINT_SIGNATURE_SYMLINK_NOT_ALLOWED")
                sig_path = None
            else:
                sig_path = raw_sig_path.resolve()
                sig_path.relative_to(root)
        except ValueError:
            problems.append("LEDGER_CHECKPOINT_SIGNATURE_PATH_ESCAPE")
            sig_path = None
        if sig_path is not None:
            if not sig_path.is_file():
                problems.append("LEDGER_CHECKPOINT_SIGNATURE_ARTIFACT_MISSING")
            elif _sha(sig_path) != sig_hash.lower():
                problems.append("LEDGER_CHECKPOINT_SIGNATURE_HASH_MISMATCH")

    trust_command = os.getenv("ACCEPTANCE_LEDGER_CHECKPOINT_VERIFY_COMMAND", "").strip()
    trust_status = "NOT_CONFIGURED"
    if trust_command and sig_path is not None:
        env = dict(os.environ)
        env.update({
            "ACCEPTANCE_LEDGER_CHECKPOINT_PATH": str(path),
            "ACCEPTANCE_LEDGER_PATH": str(ledger_path),
            "ACCEPTANCE_LEDGER_CHECKPOINT_SIGNATURE_PATH": str(sig_path),
        })
        try:
            proc = run_captured(
                ["bash", "-lc", trust_command], cwd=root, env=env, timeout=60,
            )
            if proc.returncode == 0:
                trust_status = "VERIFIED_BY_EXTERNAL_COMMAND"
            else:
                trust_status = "EXTERNAL_COMMAND_REJECTED"
                problems.append("LEDGER_CHECKPOINT_EXTERNAL_TRUST_FAILED")
        except Exception as exc:
            trust_status = f"EXTERNAL_COMMAND_ERROR:{type(exc).__name__}"
            problems.append("LEDGER_CHECKPOINT_EXTERNAL_TRUST_ERROR")
    elif require_external_trust:
        problems.append("LEDGER_CHECKPOINT_EXTERNAL_TRUST_VERIFIER_MISSING")

    return {
        "verified": not problems,
        "problems": problems,
        "sha256": _sha(path),
        "ledger_head_hash": ledger.get("head_hash"),
        "ledger_entries": ledger.get("entries"),
        "trust_status": trust_status,
        "trust_verified": trust_status == "VERIFIED_BY_EXTERNAL_COMMAND",
    }
