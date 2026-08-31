from __future__ import annotations

import json
import subprocess
from pathlib import Path

from backend.app.release.acceptance_challenge import create_challenge, verify_challenge


def _git(root: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.email", "p173@example.invalid"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.name", "P173"], cwd=root, check=True)
    (root / "seed").write_text("x", encoding="utf-8")
    subprocess.run(["git", "add", "seed"], cwd=root, check=True)
    subprocess.run(["git", "commit", "-qm", "seed"], cwd=root, check=True)


def test_trusted_production_challenge_requires_current_schema(tmp_path: Path, monkeypatch) -> None:
    _git(tmp_path)
    path = tmp_path / "reports" / "external_acceptance" / "release_challenge.json"
    path.parent.mkdir(parents=True)
    create_challenge(tmp_path, path)
    monkeypatch.setenv("ACCEPTANCE_CHALLENGE_VERIFY_COMMAND", 'test -f "$ACCEPTANCE_CHALLENGE_PATH"')

    current = verify_challenge(path, root=tmp_path, require_trust=True)
    assert current["verified"] is True
    assert current["schema_version"] == "2.3"

    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["schema_version"] = "2.2"
    path.write_text(json.dumps(payload), encoding="utf-8")

    historical = verify_challenge(path, root=tmp_path, require_trust=False)
    assert historical["verified"] is True

    strict = verify_challenge(path, root=tmp_path, require_trust=True)
    assert strict["verified"] is False
    assert "CHALLENGE_CURRENT_SCHEMA_REQUIRED" in strict["problems"]
