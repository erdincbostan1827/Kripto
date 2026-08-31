from pathlib import Path

from scripts import bootstrap_dependency_locks as mod


def _project(tmp_path: Path) -> Path:
    (tmp_path / "frontend").mkdir()
    (tmp_path / "pyproject.toml").write_text('[project]\nname="x"\nversion="0.0.0"\n', encoding="utf-8")
    (tmp_path / "frontend" / "package.json").write_text('{"name":"x","version":"0.0.0"}', encoding="utf-8")
    return tmp_path


def test_bootstrap_is_atomic_when_one_ecosystem_fails(tmp_path, monkeypatch):
    root = _project(tmp_path)
    (root / "uv.lock").write_text("old-python", encoding="utf-8")
    (root / "frontend" / "package-lock.json").write_text("old-js", encoding="utf-8")

    def fake_run(cmd, cwd, *, offline):
        if cmd[0] == "uv":
            (cwd / "uv.lock").write_text("new-python", encoding="utf-8")
            return {"command": cmd, "exit_code": 0, "ok": True, "blocker": None, "output": ""}
        return {"command": cmd, "exit_code": 1, "ok": False, "blocker": "EXIT_CODE:1", "output": "registry unavailable"}

    monkeypatch.setattr(mod, "_run", fake_run)
    result = mod.bootstrap(root=root)
    assert result["committed"] is False
    assert (root / "uv.lock").read_text() == "old-python"
    assert (root / "frontend" / "package-lock.json").read_text() == "old-js"


def test_bootstrap_commits_both_locks_only_after_both_resolve(tmp_path, monkeypatch):
    root = _project(tmp_path)

    def fake_run(cmd, cwd, *, offline):
        target = cwd / ("uv.lock" if cmd[0] == "uv" else "package-lock.json")
        target.write_text("resolved-" + cmd[0], encoding="utf-8")
        return {"command": cmd, "exit_code": 0, "ok": True, "blocker": None, "output": "ok"}

    monkeypatch.setattr(mod, "_run", fake_run)
    result = mod.bootstrap(root=root, offline=True)
    assert result["committed"] is True
    assert (root / "uv.lock").read_text() == "resolved-uv"
    assert (root / "frontend" / "package-lock.json").read_text() == "resolved-npm"
    assert result["atomic_policy"] == "BOTH_OR_NONE"
