from __future__ import annotations

import json
import subprocess
from pathlib import Path

import scripts.ci_build_evidence_manifest as transfer
import scripts.ci_toolchain_receipt as tools

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github/workflows/production-acceptance.yml"


def _repo(root: Path) -> str:
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.email", "phase149@example.invalid"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.name", "Phase 149"], cwd=root, check=True)
    (root / "seed").write_text("x", encoding="utf-8")
    subprocess.run(["git", "add", "seed"], cwd=root, check=True)
    subprocess.run(["git", "commit", "-qm", "seed"], cwd=root, check=True)
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()


def _inputs(root: Path) -> None:
    for rel in transfer.INPUTS:
        p = root / rel
        if rel in {"frontend/dist", "reports/local_acceptance"}:
            p.mkdir(parents=True, exist_ok=True)
            (p / "x.txt").write_text(rel, encoding="utf-8")
        else:
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(rel, encoding="utf-8")


def test_transfer_manifest_binds_github_run_context(tmp_path: Path, monkeypatch):
    sha = _repo(tmp_path)
    _inputs(tmp_path)
    monkeypatch.setenv("GITHUB_REPOSITORY", "owner/repo")
    monkeypatch.setenv("GITHUB_RUN_ID", "123")
    monkeypatch.setenv("GITHUB_RUN_ATTEMPT", "2")
    monkeypatch.setenv("GITHUB_WORKFLOW_REF", "owner/repo/.github/workflows/production-acceptance.yml@refs/tags/v1")
    out = tmp_path / "reports/CI_BUILD_EVIDENCE_MANIFEST.json"
    payload = transfer.create(tmp_path, out)
    assert payload["schema_version"] == "1.1"
    ok = transfer.verify(out, root=tmp_path, expected_git_sha=sha, expected_repository="owner/repo", expected_run_id="123", expected_run_attempt="2", expected_workflow_ref=payload["ci_context"]["workflow_ref"])
    assert ok["verified"]
    bad = transfer.verify(out, root=tmp_path, expected_git_sha=sha, expected_run_id="999")
    assert not bad["verified"]
    assert "CI_BUILD_EVIDENCE_CONTEXT_MISMATCH:run_id" in bad["problems"]


def test_toolchain_receipt_emits_exact_pip_specs(tmp_path: Path, monkeypatch):
    sha = _repo(tmp_path)
    versions = {name: f"1.2.{i}" for i, name in enumerate(tools.PYTHON_PACKAGES)}
    monkeypatch.setattr(tools, "_versions", lambda: versions.copy())
    out = tmp_path / "reports/CI_TOOLCHAIN_RECEIPT.json"
    payload = tools.create(tmp_path, out)
    assert payload["git_commit_sha"] == sha
    specs = tools.pip_specs(out)
    assert specs == [f"{name}=={versions[name]}" for name in tools.PYTHON_PACKAGES]
    result = tools.verify(out, root=tmp_path, expected_git_sha=sha, verify_installed=True)
    assert result["verified"]


def test_toolchain_receipt_detects_installed_version_drift(tmp_path: Path, monkeypatch):
    sha = _repo(tmp_path)
    versions = {name: "1.0" for name in tools.PYTHON_PACKAGES}
    monkeypatch.setattr(tools, "_versions", lambda: versions.copy())
    out = tmp_path / "reports/CI_TOOLCHAIN_RECEIPT.json"
    tools.create(tmp_path, out)
    drift = versions.copy()
    drift["semgrep"] = "2.0"
    monkeypatch.setattr(tools, "_versions", lambda: drift.copy())
    result = tools.verify(out, root=tmp_path, expected_git_sha=sha, verify_installed=True)
    assert not result["verified"]
    assert "CI_TOOLCHAIN_INSTALLED_VERSION_MISMATCH:semgrep" in result["problems"]


def test_production_acceptance_uses_pinned_uv_and_transferred_exact_toolchain():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "UV_VERSION: '0.12.9'" in text
    assert '"uv==${UV_VERSION}"' in text
    assert "ci_toolchain_receipt.py create" in text
    assert "CI_TOOLCHAIN_RECEIPT.json" in text
    assert "ci_toolchain_receipt.py pip-specs" in text
    assert "--verify-installed" in text
    assert "--expected-repository \"${{ github.repository }}\"" in text
    assert "--expected-run-id \"${{ github.run_id }}\"" in text
    assert "--expected-run-attempt \"${{ github.run_attempt }}\"" in text
    assert "--expected-workflow-ref \"${{ github.workflow_ref }}\"" in text
