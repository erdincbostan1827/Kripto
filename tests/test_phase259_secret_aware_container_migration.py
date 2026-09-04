from __future__ import annotations

import os
from pathlib import Path

import pytest

from scripts import run_container_migrations


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "backend" / "app" / "release" / "acceptance_contract.py"


def test_build_alembic_config_bootstraps_secret_backed_database_url(monkeypatch: pytest.MonkeyPatch) -> None:
    database_url = "postgresql+psycopg://trading:pa%ss@postgres:5432/trading"
    monkeypatch.delenv("DATABASE_URL", raising=False)

    def fake_bootstrap() -> None:
        os.environ["DATABASE_URL"] = database_url

    monkeypatch.setattr(run_container_migrations, "bootstrap_environment", fake_bootstrap)

    config = run_container_migrations.build_alembic_config()

    assert config.config_file_name == "/app/alembic.ini"
    assert config.get_main_option("sqlalchemy.url") == database_url


def test_build_alembic_config_fails_closed_without_database_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setattr(run_container_migrations, "bootstrap_environment", lambda: None)

    with pytest.raises(RuntimeError, match="DATABASE_URL unavailable"):
        run_container_migrations.build_alembic_config()


def test_main_runs_head_migration_and_propagates_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    sentinel_config = object()
    calls: list[tuple[object, str]] = []
    monkeypatch.setattr(run_container_migrations, "build_alembic_config", lambda: sentinel_config)

    def fail_upgrade(config: object, revision: str) -> None:
        calls.append((config, revision))
        raise RuntimeError("migration failed")

    monkeypatch.setattr(run_container_migrations.command, "upgrade", fail_upgrade)

    with pytest.raises(RuntimeError, match="migration failed"):
        run_container_migrations.main()

    assert calls == [(sentinel_config, "head")]


def test_runtime_acceptance_contract_uses_secret_aware_migration_runner() -> None:
    text = CONTRACT.read_text(encoding="utf-8")

    assert '("postgres_migration", ("docker", "compose", "run", "--rm", "app", "python", "-m", "scripts.run_container_migrations"), True)' in text
    assert '("postgres_migration", ("docker", "compose", "run", "--rm", "app", "alembic", "upgrade", "head"), True)' not in text
