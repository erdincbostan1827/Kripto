from pathlib import Path

import pytest

from scripts import bootstrap_dependency_locks as mod


def _project(tmp_path: Path, *, with_old_locks: bool = True) -> Path:
    (tmp_path / "frontend").mkdir()
    (tmp_path / "pyproject.toml").write_text('[project]\nname="x"\nversion="0.0.0"\n', encoding="utf-8")
    (tmp_path / "frontend" / "package.json").write_text('{"name":"x","version":"0.0.0"}', encoding="utf-8")
    if with_old_locks:
        (tmp_path / "uv.lock").write_text("old-python", encoding="utf-8")
        (tmp_path / "frontend" / "package-lock.json").write_text("old-js", encoding="utf-8")
    return tmp_path


def _successful_resolver(cmd, cwd, *, offline):
    target = cwd / ("uv.lock" if cmd[0] == "uv" else "package-lock.json")
    target.write_text("resolved-" + cmd[0], encoding="utf-8")
    return {"command": cmd, "exit_code": 0, "ok": True, "blocker": None, "output": "ok"}


def test_phase184_second_lock_promotion_failure_rolls_back_both_canonical_locks(tmp_path, monkeypatch):
    root = _project(tmp_path)
    monkeypatch.setattr(mod, "_run", _successful_resolver)
    real_promote = mod._promote_file
    calls = {"count": 0}

    def fail_second(source, target):
        calls["count"] += 1
        if calls["count"] == 2:
            raise OSError("simulated second promotion failure")
        real_promote(source, target)

    monkeypatch.setattr(mod, "_promote_file", fail_second)
    with pytest.raises(OSError):
        mod.bootstrap(root=root)

    assert (root / "uv.lock").read_text(encoding="utf-8") == "old-python"
    assert (root / "frontend" / "package-lock.json").read_text(encoding="utf-8") == "old-js"
    assert not (root / mod.TRANSACTION_JOURNAL).exists()
    assert not list(root.glob(mod.TRANSACTION_PREFIX + "*"))


def test_phase184_hard_interruption_between_promotions_is_recovered_on_next_start(tmp_path, monkeypatch):
    root = _project(tmp_path)
    monkeypatch.setattr(mod, "_run", _successful_resolver)
    real_promote = mod._promote_file
    calls = {"count": 0}

    def interrupt_second(source, target):
        calls["count"] += 1
        if calls["count"] == 2:
            raise KeyboardInterrupt("simulated abrupt process termination")
        real_promote(source, target)

    monkeypatch.setattr(mod, "_promote_file", interrupt_second)
    with pytest.raises(KeyboardInterrupt):
        mod.bootstrap(root=root)

    assert (root / "uv.lock").read_text(encoding="utf-8") == "resolved-uv"
    assert (root / "frontend" / "package-lock.json").read_text(encoding="utf-8") == "old-js"
    assert (root / mod.TRANSACTION_JOURNAL).is_file()

    recovered = mod.recover_incomplete_transaction(root)
    assert recovered == {"recovered": True, "status": "ROLLED_BACK_INTERRUPTED_TRANSACTION"}
    assert (root / "uv.lock").read_text(encoding="utf-8") == "old-python"
    assert (root / "frontend" / "package-lock.json").read_text(encoding="utf-8") == "old-js"
    assert not (root / mod.TRANSACTION_JOURNAL).exists()
    assert not list(root.glob(mod.TRANSACTION_PREFIX + "*"))


def test_phase184_failed_first_install_promotion_restores_original_absence(tmp_path, monkeypatch):
    root = _project(tmp_path, with_old_locks=False)
    monkeypatch.setattr(mod, "_run", _successful_resolver)
    real_promote = mod._promote_file
    calls = {"count": 0}

    def fail_second(source, target):
        calls["count"] += 1
        if calls["count"] == 2:
            raise OSError("simulated second promotion failure")
        real_promote(source, target)

    monkeypatch.setattr(mod, "_promote_file", fail_second)
    with pytest.raises(OSError):
        mod.bootstrap(root=root)

    assert not (root / "uv.lock").exists()
    assert not (root / "frontend" / "package-lock.json").exists()
    assert not (root / mod.TRANSACTION_JOURNAL).exists()


def test_phase184_invalid_recovery_journal_fails_closed_without_touching_locks(tmp_path):
    root = _project(tmp_path)
    (root / mod.TRANSACTION_JOURNAL).write_text(
        '{"schema_version":"1.0","classification":"DEPENDENCY_LOCK_PROMOTION_TRANSACTION","transaction_dir":"../escape","before":{}}',
        encoding="utf-8",
    )
    with pytest.raises(RuntimeError, match="LOCK_TRANSACTION_DIR_OUTSIDE_ROOT"):
        mod.recover_incomplete_transaction(root)
    assert (root / "uv.lock").read_text(encoding="utf-8") == "old-python"
    assert (root / "frontend" / "package-lock.json").read_text(encoding="utf-8") == "old-js"


def test_phase184_installers_recover_lock_transaction_before_secrets_or_build():
    root = Path(__file__).resolve().parents[2]
    linux = (root / "install.sh").read_text(encoding="utf-8")
    windows = (root / "INSTALL_WINDOWS.ps1").read_text(encoding="utf-8")
    for text in (linux, windows):
        assert "bootstrap_dependency_locks.py --recover-only" in text
        assert "bootstrap_dependency_locks.py" in text
        assert "uv.lock" in text and "frontend/package-lock.json" in text
        assert text.index("bootstrap_dependency_locks.py --recover-only") < text.index("bootstrap_secrets.py")
        assert "npm install --package-lock-only" not in text
