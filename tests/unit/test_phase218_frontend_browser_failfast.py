from __future__ import annotations

from pathlib import Path

import scripts.external.frontend_browser_acceptance as browser


def test_phase218_browser_acceptance_uses_bounded_fail_fast_npm_ci_flags():
    source = Path(browser.__file__).read_text(encoding="utf-8")
    assert '"npm", "ci", "--ignore-scripts"' in source
    assert '"--no-audit", "--no-fund"' in source
    assert '"--prefer-offline", "--fetch-retries=0", "--fetch-timeout=15000"' in source


def test_phase218_failed_npm_ci_removes_partial_dependency_tree(tmp_path: Path, monkeypatch):
    frontend = tmp_path / "frontend"
    frontend.mkdir()
    (frontend / "package-lock.json").write_text("{}", encoding="utf-8")
    node_modules = frontend / "node_modules"
    node_modules.mkdir()
    (node_modules / "partial.txt").write_text("partial", encoding="utf-8")

    monkeypatch.setattr(browser, "ROOT", tmp_path)
    monkeypatch.setattr(browser, "FRONTEND", frontend)
    monkeypatch.setattr(browser, "REPORTS", tmp_path / "reports")
    monkeypatch.setattr(browser, "OUT", tmp_path / "reports" / "frontend_browser_acceptance.json")
    monkeypatch.setattr(browser.shutil, "which", lambda tool: f"/fake/{tool}")
    monkeypatch.setattr(browser, "_git_sha", lambda: "a" * 40)

    def fake_run(command, **kwargs):
        if command[-1:] == ["--version"]:
            return {"status": "PASS", "blocker": None, "output": "Chromium 144"}
        if command[:2] == ["npm", "ci"]:
            return {"status": "BLOCKED", "blocker": "TIMEOUT", "output": ""}
        raise AssertionError(command)

    monkeypatch.setattr(browser, "_run", fake_run)
    result = browser.run(timeout=1, confirm_real=True)
    assert result["verified"] is False
    assert "TIMEOUT" in result["blockers"]
    assert result["evidence"]["npm_ci"]["partial_node_modules_removed"] is True
    assert not node_modules.exists()
