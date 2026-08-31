from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
import json
import subprocess

from backend.app.release.acceptance_challenge import create_challenge
from backend.app.release.evidence_ledger import append_entry, verify_ledger
from backend.app.release.evidence_ledger_checkpoint import verify_ledger_checkpoint


def _git(root: Path) -> str:
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.email", "p159@example.invalid"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.name", "P159"], cwd=root, check=True)
    (root / "seed").write_text("x", encoding="utf-8")
    subprocess.run(["git", "add", "seed"], cwd=root, check=True)
    subprocess.run(["git", "commit", "-qm", "seed"], cwd=root, check=True)
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()


def _checkpoint(root: Path, monkeypatch) -> tuple[Path, Path, dict]:
    git_sha = _git(root)
    reports = root / "reports" / "external_acceptance"
    reports.mkdir(parents=True, exist_ok=True)
    challenge_path = reports / "release_challenge.json"
    challenge = create_challenge(root, challenge_path)
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
    doc = {
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
    checkpoint = reports / "evidence_ledger_checkpoint.json"
    checkpoint.write_text(json.dumps(doc), encoding="utf-8")
    monkeypatch.setenv("ACCEPTANCE_CHALLENGE_VERIFY_COMMAND", "true")
    monkeypatch.setenv("ACCEPTANCE_LEDGER_CHECKPOINT_VERIFY_COMMAND", "true")
    return checkpoint, ledger_path, env


def test_signed_ledger_checkpoint_binds_current_head_challenge_git_and_environment(tmp_path: Path, monkeypatch) -> None:
    checkpoint, _, env = _checkpoint(tmp_path, monkeypatch)
    result = verify_ledger_checkpoint(checkpoint, root=tmp_path, expected_environment=env)
    assert result["verified"] is True
    assert result["trust_verified"] is True


def test_signed_ledger_checkpoint_rejects_ledger_rewrite(tmp_path: Path, monkeypatch) -> None:
    checkpoint, ledger_path, env = _checkpoint(tmp_path, monkeypatch)
    doc = json.loads(ledger_path.read_text(encoding="utf-8"))
    doc["entries"][0]["profile"] = "runtime"
    ledger_path.write_text(json.dumps(doc), encoding="utf-8")
    result = verify_ledger_checkpoint(checkpoint, root=tmp_path, expected_environment=env)
    assert result["verified"] is False
    assert "LEDGER_CHECKPOINT_LEDGER_INVALID" in result["problems"]


def test_signed_ledger_checkpoint_requires_external_signature_verifier(tmp_path: Path, monkeypatch) -> None:
    checkpoint, _, env = _checkpoint(tmp_path, monkeypatch)
    monkeypatch.delenv("ACCEPTANCE_LEDGER_CHECKPOINT_VERIFY_COMMAND")
    result = verify_ledger_checkpoint(checkpoint, root=tmp_path, expected_environment=env)
    assert result["verified"] is False
    assert "LEDGER_CHECKPOINT_EXTERNAL_TRUST_VERIFIER_MISSING" in result["problems"]


def test_strict_aggregate_verifier_contract_requires_signed_ledger_checkpoint() -> None:
    text = Path("scripts/verify_external_acceptance.py").read_text(encoding="utf-8")
    assert 'schema_version == "4.1" and profile == "all"' in text
    assert "verify_ledger_checkpoint" in text
    workflow = Path(".github/workflows/production-acceptance.yml").read_text(encoding="utf-8")
    assert "LEDGER_CHECKPOINT_SIGN_COMMAND" in workflow
    assert "ACCEPTANCE_LEDGER_CHECKPOINT_VERIFY_COMMAND" in workflow


def test_external_execution_plan_reuses_single_parsed_matrix_document() -> None:
    text = Path("scripts/verify_external_execution_plan.py").read_text(encoding="utf-8")
    assert "build_requirement_blockers(MATRIX, matrix_doc=doc)" in text
