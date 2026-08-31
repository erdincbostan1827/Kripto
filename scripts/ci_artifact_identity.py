from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports" / "CI_BUILD_ARTIFACT_IDENTITY.json"
DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
ID_RE = re.compile(r"^[1-9][0-9]*$")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def git_sha(root: Path) -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()


def bind(
    *,
    artifact_id: str,
    artifact_digest: str,
    artifact_name: str,
    expected_git_sha: str,
    root: Path = ROOT,
    output: Path | None = None,
) -> dict:
    problems: list[str] = []
    actual_git = git_sha(root)
    if actual_git != expected_git_sha:
        problems.append("CI_ARTIFACT_IDENTITY_GIT_MISMATCH")
    if not ID_RE.fullmatch(artifact_id or ""):
        problems.append("CI_ARTIFACT_ID_INVALID")
    if not DIGEST_RE.fullmatch((artifact_digest or "").lower()):
        problems.append("CI_ARTIFACT_DIGEST_INVALID")
    if not artifact_name or expected_git_sha not in artifact_name:
        problems.append("CI_ARTIFACT_NAME_NOT_BOUND_TO_GIT")
    manifest = root / "reports" / "CI_BUILD_EVIDENCE_MANIFEST.json"
    if not manifest.is_file():
        problems.append("CI_BUILD_EVIDENCE_MANIFEST_MISSING")

    payload = {
        "schema_version": "1.0",
        "classification": "GITHUB_ACTIONS_BUILD_ARTIFACT_IDENTITY_BINDING",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "verified": not problems,
        "problems": problems,
        "git_commit_sha": actual_git,
        "artifact_id": artifact_id,
        "artifact_digest": artifact_digest.lower() if isinstance(artifact_digest, str) else artifact_digest,
        "artifact_name": artifact_name,
        "build_evidence_manifest_sha256": sha256_file(manifest) if manifest.is_file() else None,
        "truth_policy": (
            "GitHub artifact digest/ID identify the uploaded workflow artifact; file-level content integrity "
            "is independently enforced by CI_BUILD_EVIDENCE_MANIFEST.json."
        ),
    }
    out = output or (root / "reports" / "CI_BUILD_ARTIFACT_IDENTITY.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-id", required=True)
    parser.add_argument("--artifact-digest", required=True)
    parser.add_argument("--artifact-name", required=True)
    parser.add_argument("--expected-git-sha", required=True)
    args = parser.parse_args()
    result = bind(
        artifact_id=args.artifact_id,
        artifact_digest=args.artifact_digest,
        artifact_name=args.artifact_name,
        expected_git_sha=args.expected_git_sha,
    )
    print(json.dumps(result, sort_keys=True))
    return 0 if result["verified"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
