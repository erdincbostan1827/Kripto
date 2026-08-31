from __future__ import annotations

import subprocess
from pathlib import Path

import scripts.lock_input_guard as guard
import scripts.lock_promotion_manifest as manifest

ROOT = Path(__file__).resolve().parents[2]


def _git(root: Path, *args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=root, text=True).strip()


def _repo(tmp_path: Path) -> tuple[Path, str]:
    root = tmp_path / "repo"
    root.mkdir()
    _git(root, "init", "-q")
    _git(root, "config", "user.email", "phase148@example.invalid")
    _git(root, "config", "user.name", "Phase 148")
    (root / "frontend").mkdir()
    (root / "pyproject.toml").write_text('[project]\nname="x"\nversion="0"\n', encoding="utf-8")
    (root / "frontend/package.json").write_text('{"name":"x","private":true}\n', encoding="utf-8")
    _git(root, "add", ".")
    _git(root, "commit", "-qm", "seed")
    return root, _git(root, "rev-parse", "HEAD")


def test_lock_input_snapshot_detects_manifest_mutation(tmp_path: Path):
    root, sha = _repo(tmp_path)
    out = root / "reports/lock-promotion/LOCK_INPUT_SNAPSHOT.json"
    guard.snapshot(root, out)
    assert guard.verify(out, root=root, expected_source_sha=sha)["verified"]
    (root / "pyproject.toml").write_text('[project]\nname="tampered"\nversion="0"\n', encoding="utf-8")
    result = guard.verify(out, root=root, expected_source_sha=sha)
    assert not result["verified"]
    assert "LOCK_INPUT_HASH_MISMATCH:pyproject.toml" in result["problems"]


def test_lock_promotion_manifest_binds_dependency_inputs(tmp_path: Path, monkeypatch):
    root, sha = _repo(tmp_path)
    (root / "uv.lock").write_text("backend-lock\n", encoding="utf-8")
    (root / "frontend/package-lock.json").write_text("{}\n", encoding="utf-8")
    monkeypatch.setattr(manifest, "cmd_version", lambda command, root: command[0] + "-version")
    out = root / "reports/lock-promotion/LOCK_PROMOTION_MANIFEST.json"
    payload = manifest.create(root, out)
    assert payload["schema_version"] == "1.1"
    assert set(payload["inputs"]) == {"pyproject.toml", "frontend/package.json"}
    assert manifest.verify(out, root=root, expected_source_sha=sha)["verified"]
    (root / "frontend/package.json").write_text('{"name":"changed"}\n', encoding="utf-8")
    result = manifest.verify(out, root=root, expected_source_sha=sha)
    assert not result["verified"]
    assert "LOCK_PROMOTION_INPUT_HASH_MISMATCH:frontend/package.json" in result["problems"]


def test_lock_promotion_workflow_is_input_guarded_and_uv_is_version_pinned():
    text = (ROOT / ".github/workflows/lock-promotion.yml").read_text(encoding="utf-8")
    assert "python scripts/lock_input_guard.py snapshot" in text
    assert "python scripts/lock_input_guard.py verify --expected-source-sha" in text
    assert "UV_VERSION: '0.10.0'" in text
    assert '"uv==${UV_VERSION}"' in text
