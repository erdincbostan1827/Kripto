from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
import json
import os
import subprocess

import pytest

from backend.app.release.acceptance_challenge import create_challenge
from backend.app.release.evidence_ledger import append_entry, verify_ledger
from backend.app.release.evidence_ledger_checkpoint import verify_ledger_checkpoint
from scripts.verify_external_acceptance import _strict_regular_artifact


def _git(root: Path) -> str:
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.email", "p171@example.invalid"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.name", "P171"], cwd=root, check=True)
    (root / "seed").write_text("x", encoding="utf-8")
    subprocess.run(["git", "add", "seed"], cwd=root, check=True)
    subprocess.run(["git", "commit", "-qm", "seed"], cwd=root, check=True)
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()


def _checkpoint(root: Path, monkeypatch) -> tuple[Path, Path, Path, dict]:
    git_sha = _git(root)
    reports = root / "reports" / "external_acceptance"
    reports.mkdir(parents=True, exist_ok=True)
    challenge = create_challenge(root, reports / "release_challenge.json")
    ledger_path = reports / "evidence_ledger.json"
    append_entry(
        ledger_path,
        manifest_sha256="a" * 64,
        challenge_id=challenge["challenge_id"],
        git_commit_sha=git_sha,
        profile="all-merged",
        root=root,
    )
    ledger = verify_ledger(ledger_path)
    sig = reports / "evidence_ledger_checkpoint.sig"
    sig.write_text("detached-signature", encoding="utf-8")
    env = {"acceptance_environment_id_hash": "b" * 64, "topology_hash": "c" * 64}
    checkpoint = reports / "evidence_ledger_checkpoint.json"
    checkpoint.write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "classification": "REAL_EXTERNAL_ACCEPTANCE_SIGNED_LEDGER_CHECKPOINT",
                "real_system": True,
                "executed": True,
                "observed_at": datetime.now(timezone.utc).isoformat(),
                "git_commit_sha": git_sha,
                "release_challenge": {"challenge_id": challenge["challenge_id"], "sha256": challenge["sha256"]},
                "environment": env,
                "ledger_artifact": "reports/external_acceptance/evidence_ledger.json",
                "ledger_sha256": sha256(ledger_path.read_bytes()).hexdigest(),
                "ledger_head_hash": ledger["head_hash"],
                "ledger_entries": ledger["entries"],
                "signature_verified": True,
                "signer_identity": "acceptance-kms@example.invalid",
                "signer_key_id": "kms-key-1",
                "signature_mechanism": "detached-kms-signature",
                "signature_artifact": "reports/external_acceptance/evidence_ledger_checkpoint.sig",
                "signature_sha256": sha256(sig.read_bytes()).hexdigest(),
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("ACCEPTANCE_CHALLENGE_VERIFY_COMMAND", "true")
    monkeypatch.setenv("ACCEPTANCE_LEDGER_CHECKPOINT_VERIFY_COMMAND", "true")
    return checkpoint, ledger_path, sig, env


def test_strict_acceptance_artifact_rejects_symlinked_parent_directory(tmp_path: Path) -> None:
    real = tmp_path / "real-run"
    real.mkdir()
    (real / "artifact.log").write_text("ok", encoding="utf-8")
    alias = tmp_path / "reports"
    os.symlink(real, alias, target_is_directory=True)
    with pytest.raises(ValueError, match="symlink component"):
        _strict_regular_artifact(tmp_path, "reports/artifact.log")


def test_signed_checkpoint_rejects_symlinked_ledger_path(tmp_path: Path, monkeypatch) -> None:
    checkpoint, ledger_path, _, env = _checkpoint(tmp_path, monkeypatch)
    real_ledger = ledger_path.with_name("evidence_ledger.real.json")
    ledger_path.rename(real_ledger)
    ledger_path.symlink_to(real_ledger.name)
    result = verify_ledger_checkpoint(checkpoint, root=tmp_path, expected_environment=env)
    assert result["verified"] is False
    assert "LEDGER_CHECKPOINT_LEDGER_SYMLINK_NOT_ALLOWED" in result["problems"]


def test_signed_checkpoint_rejects_symlinked_signature_path(tmp_path: Path, monkeypatch) -> None:
    checkpoint, _, sig, env = _checkpoint(tmp_path, monkeypatch)
    real_sig = sig.with_name("checkpoint.real.sig")
    sig.rename(real_sig)
    sig.symlink_to(real_sig.name)
    result = verify_ledger_checkpoint(checkpoint, root=tmp_path, expected_environment=env)
    assert result["verified"] is False
    assert "LEDGER_CHECKPOINT_SIGNATURE_SYMLINK_NOT_ALLOWED" in result["problems"]


def test_ledger_append_refuses_symlink_target(tmp_path: Path) -> None:
    reports = tmp_path / "reports" / "external_acceptance"
    reports.mkdir(parents=True)
    real = reports / "real-ledger.json"
    real.write_text('{"schema_version":"1.0","classification":"EXTERNAL_ACCEPTANCE_APPEND_ONLY_EVIDENCE_LEDGER","entries":[]}', encoding="utf-8")
    link = reports / "evidence_ledger.json"
    link.symlink_to(real.name)
    with pytest.raises(ValueError, match="symlink component"):
        append_entry(link, manifest_sha256="a" * 64, challenge_id="challenge-123456789", git_commit_sha="b" * 40, profile="runtime", root=tmp_path)

from scripts.package_release import build_release
from scripts.package_evidence import build_evidence_archive, verify_evidence_archive
from scripts.package_distribution import verify_distribution
import zipfile


def test_source_release_rejects_symlinked_source_file(tmp_path: Path) -> None:
    root = tmp_path / "project"
    root.mkdir()
    outside = tmp_path / "outside.txt"
    outside.write_text("sensitive", encoding="utf-8")
    (root / "leak.txt").symlink_to(outside)
    with pytest.raises(ValueError, match="SOURCE_RELEASE_SYMLINK_NOT_ALLOWED"):
        build_release(root, tmp_path / "source.zip")


def test_evidence_bundle_rejects_escaping_manifest_reference(tmp_path: Path, monkeypatch) -> None:
    root = tmp_path / "project"
    reports = root / "reports" / "external_acceptance"
    reports.mkdir(parents=True)
    outside = tmp_path / "outside.json"
    outside.write_text("{}", encoding="utf-8")
    (reports / "manifest_all.json").write_text(
        json.dumps({
            "evidence": [],
            "source_profiles": {
                "runtime": {"reference": "reports/external_acceptance/../../../outside.json"}
            },
        }),
        encoding="utf-8",
    )
    monkeypatch.setattr("scripts.package_evidence.git_sha", lambda _root: "a" * 40)
    with pytest.raises(ValueError, match="EVIDENCE_REFERENCE_UNSAFE"):
        build_evidence_archive(root=root, archive=tmp_path / "evidence.zip")


def test_evidence_bundle_rejects_symlinked_referenced_file(tmp_path: Path, monkeypatch) -> None:
    root = tmp_path / "project"
    reports = root / "reports" / "external_acceptance"
    reports.mkdir(parents=True)
    target = reports / "runtime.real.json"
    target.write_text("{}", encoding="utf-8")
    link = reports / "runtime.json"
    link.symlink_to(target.name)
    (reports / "manifest_all.json").write_text(
        json.dumps({"evidence": [], "source_profiles": {"runtime": {"reference": "reports/external_acceptance/runtime.json"}}}),
        encoding="utf-8",
    )
    monkeypatch.setattr("scripts.package_evidence.git_sha", lambda _root: "a" * 40)
    with pytest.raises(ValueError, match="EVIDENCE_REFERENCE_SYMLINK_NOT_ALLOWED"):
        build_evidence_archive(root=root, archive=tmp_path / "evidence.zip")


def test_evidence_archive_verifier_rejects_unexpected_member(tmp_path: Path, monkeypatch) -> None:
    root = tmp_path / "project"
    root.mkdir()
    (root / "RELEASE_MANIFEST.json").write_text("{}", encoding="utf-8")
    monkeypatch.setattr("scripts.package_evidence.git_sha", lambda _root: "a" * 40)
    archive = tmp_path / "evidence.zip"
    build_evidence_archive(root=root, archive=archive)
    with zipfile.ZipFile(archive, "a") as zf:
        zf.writestr("unexpected.txt", b"tamper")
    result = verify_evidence_archive(archive)
    assert result["verified"] is False
    assert "UNEXPECTED_MEMBER:unexpected.txt" in result["problems"]


def test_distribution_verifier_rejects_unexpected_member(tmp_path: Path) -> None:
    archive = tmp_path / "distribution.zip"
    manifest = {
        "schema_version": "1.0",
        "default_mode": "PAPER",
        "live_enabled": False,
        "artifacts": [],
    }
    with zipfile.ZipFile(archive, "w") as zf:
        zf.writestr("RELEASE_BUNDLE.json", json.dumps(manifest))
        zf.writestr("SHA256SUMS.txt", b"")
        zf.writestr("unexpected.bin", b"tamper")
    result = verify_distribution(archive)
    assert result["verified"] is False
    assert "UNEXPECTED_MEMBER:unexpected.bin" in result["problems"]
