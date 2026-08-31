from __future__ import annotations

import subprocess
from pathlib import Path

from scripts.production_acceptance_handoff import build_handoff

ROOT = Path(__file__).resolve().parents[2]


def _git(root: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=root, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def _repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    root.mkdir()
    _git(root, "init", "-q")
    _git(root, "config", "user.email", "test@example.com")
    _git(root, "config", "user.name", "Test")
    (root / "x").write_text("x\n")
    _git(root, "add", "x")
    _git(root, "commit", "-qm", "init")
    return root


def test_lock_promotion_requires_immutable_ref_and_preserves_validation_receipt():
    text = (ROOT / ".github/workflows/lock-promotion.yml").read_text()
    assert 'validate_acceptance_ref.py "${{ github.event.inputs.source_ref }}"' in text
    assert "SOURCE_REF_VALIDATION.json" in text
    assert "contents: read" in text
    assert "git push" not in text


def test_handoff_reports_source_lock_compliance_not_presence_only(tmp_path):
    root = _repo(tmp_path)
    (root / "uv.lock").write_text("generated\n")
    (root / "frontend").mkdir()
    (root / "frontend/package-lock.json").write_text("{}\n")
    payload = build_handoff(root)
    assert payload["schema_version"] == "1.2"
    assert payload["source_file_presence"] == {"uv.lock": True, "frontend/package-lock.json": True}
    assert payload["source_lock_compliance"]["verified"] is False
    assert set(payload["source_lock_compliance"]["problems"]) == {
        "uv.lock:NOT_TRACKED_IN_HEAD",
        "frontend/package-lock.json:NOT_TRACKED_IN_HEAD",
    }


def test_handoff_direct_cli_import_path_works():
    proc = subprocess.run(
        ["python", "scripts/production_acceptance_handoff.py"], cwd=ROOT,
        text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False,
    )
    assert proc.returncode == 0, proc.stdout
    assert "ACCEPTANCE_HANDOFF_NOT_ACCEPTANCE_EVIDENCE" in proc.stdout
