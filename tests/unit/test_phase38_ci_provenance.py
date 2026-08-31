from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

import scripts.external.provenance_capture as pc
import scripts.external_acceptance_runner as runner
import scripts.verify_external_acceptance as verifier


def _repo(tmp_path: Path) -> tuple[Path, str]:
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=tmp_path, check=True)
    (tmp_path / "seed").write_text("x")
    subprocess.run(["git", "add", "seed"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "seed"], cwd=tmp_path, check=True)
    sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=tmp_path, text=True).strip()
    return tmp_path, sha


def test_provenance_capture_fails_outside_ci(tmp_path: Path):
    root, sha = _repo(tmp_path)
    with pytest.raises(RuntimeError, match="CI environment"):
        pc.capture(root=root, env={})


def test_provenance_capture_requires_matching_commit(tmp_path: Path):
    root, sha = _repo(tmp_path)
    with pytest.raises(RuntimeError, match="does not match"):
        pc.capture(root=root, env={"CI": "true", "CI_RUN_ID": "1", "CI_COMMIT_SHA": "0" * 40})


def test_provenance_profile_is_part_of_all_external_acceptance():
    keys = {key for key, _, _ in runner.build_plan("all")}
    assert {"ci_provenance_capture", "artifact_sign_verify"} <= keys
    assert verifier.GROUP_KEYS["provenance"] == ("ci_provenance_capture", "artifact_sign_verify")


def test_provenance_capture_hashes_real_build_inputs(tmp_path: Path, monkeypatch):
    root, sha = _repo(tmp_path)
    (root / "frontend/dist").mkdir(parents=True)
    (root / "frontend/dist/app.js").write_text("console.log(1)")
    (root / "frontend/package-lock.json").write_text("{}")
    (root / "uv.lock").write_text("version = 1")
    (root / "reports/external_acceptance").mkdir(parents=True)
    (root / "reports/external_acceptance/sbom.cdx.json").write_text("{}")
    (root / "reports/external_acceptance/dependency_licenses.json").write_text("[]")
    (root / "reports/external_acceptance/supply_chain_artifact_verification.json").write_text("{}")
    (root / "reports/external_acceptance/scanner_image_digests.json").write_text(json.dumps({
        "schema_version": "1.0",
        "classification": "CI_SCANNER_IMAGE_DIGEST_RECEIPT",
        "scanners": {
            "gitleaks": {"requested_image": "ghcr.io/gitleaks/gitleaks:v8.28.0", "resolved_digest": "ghcr.io/gitleaks/gitleaks@sha256:" + "a" * 64},
            "trivy": {"requested_image": "aquasec/trivy:0.65.0", "resolved_digest": "aquasec/trivy@sha256:" + "b" * 64},
            "syft": {"requested_image": "anchore/syft:v1.32.0", "resolved_digest": "anchore/syft@sha256:" + "c" * 64},
        },
    }))
    monkeypatch.setattr(pc, "container_digest", lambda image, root: "repo@sha256:" + "a" * 64)
    out = pc.capture(root=root, env={"CI": "true", "CI_RUN_ID": "42", "CI_COMMIT_SHA": sha, "ACCEPTANCE_CONTAINER_IMAGE": "repo:test"})
    assert out["ci_run_id"] == "42" and out["git_commit_sha"] == sha
    assert len(out["dependency_lock_hash"]) == 64 and len(out["frontend_artifact_hash"]) == 64
    assert len(out["scanner_image_digest_manifest_hash"]) == 64
    assert out["container_digest"].startswith("repo@sha256:")
