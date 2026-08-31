from pathlib import Path
import subprocess

from backend.app.release.acceptance_challenge import create_challenge, verify_challenge


def _git(root: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.email", "phase69@example.invalid"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.name", "Phase69"], cwd=root, check=True)
    (root / "seed").write_text("seed\n", encoding="utf-8")
    subprocess.run(["git", "add", "seed"], cwd=root, check=True)
    subprocess.run(["git", "commit", "-qm", "seed"], cwd=root, check=True)


def test_challenge_trust_is_not_claimed_without_verifier(tmp_path, monkeypatch):
    _git(tmp_path)
    path = tmp_path / "reports/external_acceptance/release_challenge.json"
    create_challenge(tmp_path, path)
    monkeypatch.delenv("ACCEPTANCE_CHALLENGE_VERIFY_COMMAND", raising=False)
    monkeypatch.delenv("ACCEPTANCE_REQUIRE_CHALLENGE_TRUST", raising=False)
    result = verify_challenge(path, root=tmp_path)
    assert result["verified"]
    assert result["trust_verified"] is False
    assert result["trust_status"] == "NOT_CONFIGURED"


def test_required_challenge_trust_fails_closed_when_verifier_missing(tmp_path, monkeypatch):
    _git(tmp_path)
    path = tmp_path / "reports/external_acceptance/release_challenge.json"
    create_challenge(tmp_path, path)
    monkeypatch.delenv("ACCEPTANCE_CHALLENGE_VERIFY_COMMAND", raising=False)
    monkeypatch.setenv("ACCEPTANCE_REQUIRE_CHALLENGE_TRUST", "1")
    result = verify_challenge(path, root=tmp_path)
    assert not result["verified"]
    assert "CHALLENGE_TRUST_VERIFIER_MISSING" in result["problems"]


def test_external_challenge_verifier_can_accept_without_exposing_command(tmp_path, monkeypatch):
    _git(tmp_path)
    path = tmp_path / "reports/external_acceptance/release_challenge.json"
    create_challenge(tmp_path, path)
    monkeypatch.setenv("ACCEPTANCE_REQUIRE_CHALLENGE_TRUST", "1")
    monkeypatch.setenv("ACCEPTANCE_CHALLENGE_VERIFY_COMMAND", 'test -f "$ACCEPTANCE_CHALLENGE_PATH"')
    result = verify_challenge(path, root=tmp_path)
    assert result["verified"]
    assert result["trust_verified"] is True
    assert result["trust_status"] == "VERIFIED_BY_EXTERNAL_COMMAND"
    assert "command" not in result


def test_external_challenge_verifier_rejection_blocks_acceptance(tmp_path, monkeypatch):
    _git(tmp_path)
    path = tmp_path / "reports/external_acceptance/release_challenge.json"
    create_challenge(tmp_path, path)
    monkeypatch.setenv("ACCEPTANCE_REQUIRE_CHALLENGE_TRUST", "1")
    monkeypatch.setenv("ACCEPTANCE_CHALLENGE_VERIFY_COMMAND", "exit 7")
    result = verify_challenge(path, root=tmp_path)
    assert not result["verified"]
    assert "CHALLENGE_TRUST_VERIFICATION_FAILED" in result["problems"]
