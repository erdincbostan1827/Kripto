from __future__ import annotations

import json
import subprocess
from pathlib import Path

from backend.app.release.acceptance_challenge import create_challenge, verify_challenge
from backend.app.release.evidence_ledger import append_entry, verify_ledger
import scripts.external_acceptance_runner as runner


def _git(root: Path) -> str:
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.email", "phase47@example.invalid"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.name", "Phase47"], cwd=root, check=True)
    (root / "seed").write_text("seed\n")
    subprocess.run(["git", "add", "seed"], cwd=root, check=True)
    subprocess.run(["git", "commit", "-qm", "seed"], cwd=root, check=True)
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()


def test_release_challenge_is_git_bound_and_hash_verifiable(tmp_path: Path) -> None:
    git_sha = _git(tmp_path)
    path = tmp_path / "reports/external_acceptance/release_challenge.json"
    created = create_challenge(tmp_path, path)
    checked = verify_challenge(path, root=tmp_path)
    assert checked["verified"] is True
    assert checked["git_commit_sha"] == git_sha
    assert checked["sha256"] == created["sha256"]


def test_challenge_from_different_commit_is_rejected(tmp_path: Path) -> None:
    _git(tmp_path)
    path = tmp_path / "challenge.json"
    create_challenge(tmp_path, path)
    (tmp_path / "second").write_text("change\n")
    subprocess.run(["git", "add", "second"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-qm", "second"], cwd=tmp_path, check=True)
    checked = verify_challenge(path, root=tmp_path)
    assert checked["verified"] is False
    assert "CHALLENGE_GIT_MISMATCH" in checked["problems"]


def test_evidence_ledger_detects_tampering_and_replay(tmp_path: Path) -> None:
    path = tmp_path / "ledger.json"
    append_entry(path, manifest_sha256="a" * 64, challenge_id="c1", git_commit_sha="g1", profile="runtime")
    append_entry(path, manifest_sha256="b" * 64, challenge_id="c2", git_commit_sha="g1", profile="testnet")
    assert verify_ledger(path)["verified"] is True
    doc = json.loads(path.read_text())
    doc["entries"][0]["profile"] = "forged"
    path.write_text(json.dumps(doc))
    assert verify_ledger(path)["verified"] is False

    replay = tmp_path / "replay.json"
    append_entry(replay, manifest_sha256="a" * 64, challenge_id="c1", git_commit_sha="g1", profile="runtime")
    append_entry(replay, manifest_sha256="a" * 64, challenge_id="c2", git_commit_sha="g1", profile="runtime")
    checked = verify_ledger(replay)
    assert checked["verified"] is False
    assert any(p.startswith("LEDGER_MANIFEST_REPLAY") for p in checked["problems"])


def test_confirm_real_without_challenge_executes_no_acceptance_commands(monkeypatch, tmp_path: Path) -> None:
    reports = tmp_path / "reports/external_acceptance"
    monkeypatch.setattr(runner, "ROOT", tmp_path)
    monkeypatch.setattr(runner, "REPORTS", reports)
    called = []
    monkeypatch.setattr(runner, "_run", lambda *a, **k: called.append((a, k)))
    payload = runner.execute("runtime", confirm_real=True, timeout=1)
    assert payload["selected_all_pass"] is False
    assert payload["blocker"] == "RELEASE_CHALLENGE_NOT_VERIFIED"
    assert called == []
