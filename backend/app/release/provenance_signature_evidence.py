from __future__ import annotations

import hashlib
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from backend.app.release.acceptance_challenge import verify_challenge
from backend.app.release.path_integrity import PathIntegrityError, strict_regular_file


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _time(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def _environment_binding(expected_environment: dict[str, Any] | None = None) -> dict[str, Any]:
    if isinstance(expected_environment, dict):
        return expected_environment
    env_id = os.getenv("ACCEPTANCE_ENVIRONMENT_ID", "")
    topology = os.getenv("ACCEPTANCE_TOPOLOGY_HASH", "").lower()
    return {
        "acceptance_environment_id_hash": hashlib.sha256(env_id.encode()).hexdigest() if env_id else None,
        "topology_hash": topology if len(topology) == 64 and all(c in "0123456789abcdef" for c in topology) else None,
    }


def verify_provenance_signature_evidence(
    path: Path,
    *,
    root: Path,
    max_age_hours: int = 168,
    strict_external: bool = False,
    expected_environment: dict[str, Any] | None = None,
) -> dict[str, Any]:
    problems: list[str] = []
    if strict_external:
        if path.is_symlink():
            return {"verified": False, "problems": ["SIGNATURE_EVIDENCE_SYMLINK_NOT_ALLOWED"]}
        try:
            path = strict_regular_file(root, path)
        except PathIntegrityError as exc:
            if "not a regular file" in str(exc):
                return {"verified": False, "problems": ["SIGNATURE_EVIDENCE_MISSING"]}
            return {"verified": False, "problems": ["SIGNATURE_EVIDENCE_PATH_INTEGRITY_INVALID"]}
    elif not path.is_file():
        return {"verified": False, "problems": ["SIGNATURE_EVIDENCE_MISSING"]}
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"verified": False, "problems": [f"SIGNATURE_EVIDENCE_INVALID_JSON:{type(exc).__name__}"]}
    if strict_external:
        if doc.get("schema_version") != "2.0":
            problems.append("SIGNATURE_EVIDENCE_STRICT_SCHEMA_REQUIRED")
    elif doc.get("schema_version") not in {"1.0", "2.0"}:
        problems.append("SIGNATURE_EVIDENCE_SCHEMA_UNSUPPORTED")
    if doc.get("classification") != "REAL_PROVENANCE_SIGNATURE_VERIFICATION":
        problems.append("SIGNATURE_EVIDENCE_CLASSIFICATION_INVALID")
    if doc.get("real_system") is not True or doc.get("executed") is not True:
        problems.append("SIGNATURE_EVIDENCE_NOT_REAL_EXECUTION")
    if doc.get("signature_verified") is not True:
        problems.append("SIGNATURE_NOT_VERIFIED")
    for key in ("signer_identity", "signature_mechanism"):
        if not isinstance(doc.get(key), str) or not doc[key].strip():
            problems.append(f"SIGNATURE_FIELD_MISSING:{key}")
    observed = _time(doc.get("observed_at"))
    if observed is None:
        problems.append("SIGNATURE_OBSERVED_AT_INVALID")
    else:
        age = (datetime.now(timezone.utc) - observed.astimezone(timezone.utc)).total_seconds() / 3600
        if age < -1 or age > max_age_hours:
            problems.append("SIGNATURE_EVIDENCE_STALE")
    try:
        git_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    except Exception:
        git_sha = None
        problems.append("SIGNATURE_GIT_UNAVAILABLE")
    if git_sha and doc.get("git_commit_sha") != git_sha:
        problems.append("SIGNATURE_GIT_MISMATCH")

    if strict_external:
        challenge = verify_challenge(
            root / "reports" / "external_acceptance" / "release_challenge.json",
            root=root,
            require_trust=True,
        )
        bound = doc.get("release_challenge") if isinstance(doc.get("release_challenge"), dict) else {}
        if not challenge.get("verified"):
            problems.append("SIGNATURE_RELEASE_CHALLENGE_NOT_VERIFIED")
        elif bound.get("challenge_id") != challenge.get("challenge_id") or bound.get("sha256") != challenge.get("sha256"):
            problems.append("SIGNATURE_RELEASE_CHALLENGE_MISMATCH")

        expected = _environment_binding(expected_environment)
        expected_env = expected.get("acceptance_environment_id_hash")
        expected_topology = expected.get("topology_hash")
        environment = doc.get("environment") if isinstance(doc.get("environment"), dict) else {}
        if not isinstance(expected_env, str) or len(expected_env) != 64:
            problems.append("SIGNATURE_EXPECTED_ENVIRONMENT_MISSING")
        elif environment.get("acceptance_environment_id_hash") != expected_env:
            problems.append("SIGNATURE_ENVIRONMENT_MISMATCH")
        if not isinstance(expected_topology, str) or len(expected_topology) != 64:
            problems.append("SIGNATURE_EXPECTED_TOPOLOGY_MISSING")
        elif environment.get("topology_hash") != expected_topology:
            problems.append("SIGNATURE_TOPOLOGY_MISMATCH")

    root_resolved = root.resolve()
    bindings = (
        ("provenance_artifact", "provenance_sha256"),
        ("signature_artifact", "signature_sha256"),
    )
    for path_key, hash_key in bindings:
        rel = doc.get(path_key)
        expected = doc.get(hash_key)
        if not isinstance(rel, str) or not rel or not isinstance(expected, str) or len(expected) != 64:
            problems.append(f"SIGNATURE_BINDING_INVALID:{path_key}")
            continue
        raw_target = root / rel
        if strict_external:
            if raw_target.is_symlink():
                problems.append(f"SIGNATURE_ARTIFACT_SYMLINK_NOT_ALLOWED:{path_key}")
                continue
            try:
                target = strict_regular_file(root, rel)
            except PathIntegrityError:
                problems.append(f"SIGNATURE_ARTIFACT_PATH_INTEGRITY_INVALID:{path_key}")
                continue
        else:
            target = raw_target.resolve()
            try:
                target.relative_to(root_resolved)
            except ValueError:
                problems.append(f"SIGNATURE_PATH_ESCAPE:{path_key}")
                continue
        if not target.is_file():
            problems.append(f"SIGNATURE_ARTIFACT_MISSING:{path_key}")
        elif _sha(target) != expected.lower():
            problems.append(f"SIGNATURE_HASH_MISMATCH:{path_key}")
    expected_prov = (root / "reports" / "external_acceptance" / "provenance.json").resolve()
    declared = doc.get("provenance_artifact")
    if isinstance(declared, str) and (root / declared).resolve() != expected_prov:
        problems.append("SIGNATURE_PROVENANCE_TARGET_INVALID")
    return {
        "verified": not problems,
        "problems": problems,
        "sha256": _sha(path),
        "git_commit_sha": doc.get("git_commit_sha"),
        "signer_identity": doc.get("signer_identity"),
        "signature_mechanism": doc.get("signature_mechanism"),
    }
