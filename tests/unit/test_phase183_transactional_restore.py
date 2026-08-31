from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_linux_restore_is_fail_closed_and_transactional():
    text = (ROOT / "scripts/restore.sh").read_text(encoding="utf-8")
    assert "set -euo pipefail" in text
    assert "umask 077" in text
    assert "invalid_target_database" in text
    assert "protected_target_database" in text
    assert "target_database_exists" in text
    assert "restore_stage_" in text
    assert "trap cleanup EXIT INT TERM" in text
    assert "pg_restore --exit-on-error" in text
    assert 'ALTER DATABASE \\"$STAGING\\" RENAME TO \\"$TARGET\\"' in text
    assert "dropdb -U trading --if-exists" in text
    assert "promotion=atomic" in text
    assert 'createdb -U trading "$TARGET"' not in text


def test_windows_restore_matches_fail_closed_transactional_contract():
    text = (ROOT / "scripts/restore.ps1").read_text(encoding="utf-8")
    for term in [
        "invalid_target_database",
        "protected_target_database",
        "target_database_exists",
        "restore_stage_",
        "pg_restore --exit-on-error",
        "ALTER DATABASE",
        "dropdb -U trading --if-exists",
        "promotion=atomic",
    ]:
        assert term in text
    assert "finally" in text


def test_restore_documentation_states_non_destructive_promotion_contract():
    text = (ROOT / "docs/UPDATE_ROLLBACK.md").read_text(encoding="utf-8")
    for term in [
        "mevcut hedef veritabanını ezmez",
        "staging veritabanı",
        "atomik rename",
        "yarım restore",
    ]:
        assert term in text
