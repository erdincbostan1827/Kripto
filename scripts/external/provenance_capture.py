from __future__ import annotations

import hashlib
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "reports" / "external_acceptance" / "provenance.json"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def tree_hash(path: Path) -> str:
    h = hashlib.sha256()
    for file in sorted(p for p in path.rglob("*") if p.is_file()):
        rel = file.relative_to(path).as_posix().encode()
        h.update(rel + b"\0" + sha256_file(file).encode() + b"\0")
    return h.hexdigest()


def git_sha(root: Path = ROOT) -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()


def container_digest(image: str, *, root: Path = ROOT) -> str:
    raw = subprocess.check_output(
        ["docker", "image", "inspect", "--format", "{{json .RepoDigests}}", image], cwd=root, text=True
    ).strip()
    digests = json.loads(raw)
    if not isinstance(digests, list) or not digests:
        raise RuntimeError("container image has no immutable RepoDigest")
    digest = str(digests[0])
    if "@sha256:" not in digest:
        raise RuntimeError("container RepoDigest is not sha256-addressed")
    return digest


def _scanner_digest_verifier():
    if __package__:
        from .verify_scanner_image_digests import verify
    else:
        from verify_scanner_image_digests import verify
    return verify


def capture(*, root: Path = ROOT, env: dict[str, str] | None = None) -> dict:
    e = dict(os.environ if env is None else env)
    if e.get("CI", "").lower() not in {"1", "true", "yes"}:
        raise RuntimeError("CI environment is required")
    run_id = e.get("GITHUB_RUN_ID") or e.get("CI_RUN_ID")
    if not run_id:
        raise RuntimeError("CI run id is required")
    actual_sha = git_sha(root)
    declared_sha = e.get("GITHUB_SHA") or e.get("CI_COMMIT_SHA")
    if declared_sha != actual_sha:
        raise RuntimeError("CI commit SHA does not match checked-out source")

    required_files = {
        "dependency_lock_hash": root / "uv.lock",
        "frontend_lock_hash": root / "frontend" / "package-lock.json",
        "sbom_hash": root / "reports" / "external_acceptance" / "sbom.cdx.json",
        "license_report_hash": root / "reports" / "external_acceptance" / "dependency_licenses.json",
        "supply_chain_verification_hash": root / "reports" / "external_acceptance" / "supply_chain_artifact_verification.json",
        "scanner_image_digest_manifest_hash": root / "reports" / "external_acceptance" / "scanner_image_digests.json",
    }
    missing = [str(p.relative_to(root)) for p in required_files.values() if not p.is_file()]
    frontend_dist = root / "frontend" / "dist"
    if not frontend_dist.is_dir() or not any(p.is_file() for p in frontend_dist.rglob("*")):
        missing.append("frontend/dist")
    image = e.get("ACCEPTANCE_CONTAINER_IMAGE")
    if not image:
        missing.append("ACCEPTANCE_CONTAINER_IMAGE")
    if missing:
        raise RuntimeError("missing provenance inputs: " + ",".join(missing))

    verify_scanner_image_digests = _scanner_digest_verifier()
    scanner_result = verify_scanner_image_digests(required_files["scanner_image_digest_manifest_hash"])
    if not scanner_result.get("verified"):
        raise RuntimeError("scanner image digest receipt is invalid: " + ",".join(scanner_result.get("problems", [])))

    payload = {
        "schema_version": "1.0",
        "classification": "REAL_CI_BUILD_PROVENANCE",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "ci_run_id": run_id,
        "git_commit_sha": actual_sha,
        **{name: sha256_file(path) for name, path in required_files.items()},
        "frontend_artifact_hash": tree_hash(frontend_dist),
        "container_digest": container_digest(image, root=root),
        "container_image": image,
    }
    return payload


def main() -> int:
    try:
        payload = capture()
    except Exception as exc:
        print(json.dumps({"status": "BLOCKED", "error_type": type(exc).__name__, "error": str(exc)}, sort_keys=True))
        return 2
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": "PASS", "artifact": str(OUT.relative_to(ROOT)), "sha256": sha256_file(OUT)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
