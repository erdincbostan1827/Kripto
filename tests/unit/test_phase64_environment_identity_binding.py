from __future__ import annotations

import json
import subprocess
from hashlib import sha256
from pathlib import Path

import scripts.external_acceptance_runner as runner
import scripts.merge_external_acceptance as merger
from backend.app.release.acceptance_challenge import create_challenge


def _git(root: Path) -> str:
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.email", "p64@example.invalid"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.name", "P64"], cwd=root, check=True)
    (root / "seed").write_text("x")
    subprocess.run(["git", "add", "seed"], cwd=root, check=True)
    subprocess.run(["git", "commit", "-qm", "seed"], cwd=root, check=True)
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()


def test_phase64_confirmed_real_requires_environment_identity_after_valid_challenge(tmp_path, monkeypatch):
    _git(tmp_path)
    reports = tmp_path / "reports/external_acceptance"
    reports.mkdir(parents=True)
    create_challenge(tmp_path, reports / "release_challenge.json")
    monkeypatch.setattr(runner, "ROOT", tmp_path)
    monkeypatch.setattr(runner, "REPORTS", reports)
    monkeypatch.setenv("ACCEPTANCE_CHALLENGE_VERIFY_COMMAND", "true")
    monkeypatch.delenv("ACCEPTANCE_ENVIRONMENT_ID", raising=False)
    monkeypatch.delenv("ACCEPTANCE_TOPOLOGY_HASH", raising=False)
    called = []
    monkeypatch.setattr(runner, "_run", lambda *a, **k: called.append((a,k)))
    result = runner.execute("runtime", confirm_real=True, timeout=1)
    assert result["selected_all_pass"] is False
    assert result["blocker"].startswith("ACCEPTANCE_ENVIRONMENT_IDENTITY_MISSING")
    assert called == []


def test_phase64_environment_manifest_hashes_id_and_preserves_topology_hash(monkeypatch):
    monkeypatch.setenv("ACCEPTANCE_ENVIRONMENT_ID", "prod-acceptance-a")
    topology = "a" * 64
    monkeypatch.setenv("ACCEPTANCE_TOPOLOGY_HASH", topology)
    env = runner._environment()
    assert env["acceptance_environment_id_hash"] == sha256(b"prod-acceptance-a").hexdigest()
    assert env["topology_hash"] == topology
    assert "prod-acceptance-a" not in json.dumps(env)


def test_phase64_workflow_passes_protected_environment_identity_vars():
    text = Path('.github/workflows/production-acceptance.yml').read_text(encoding='utf-8')
    assert '${{ vars.ACCEPTANCE_ENVIRONMENT_ID }}' in text
    assert '${{ vars.ACCEPTANCE_TOPOLOGY_HASH }}' in text
