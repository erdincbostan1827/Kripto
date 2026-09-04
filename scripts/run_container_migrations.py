from __future__ import annotations

import os
from pathlib import Path

from alembic import command
from alembic.config import Config

from scripts.container_entrypoint import bootstrap_environment


ALEMBIC_INI = Path("/app/alembic.ini")


def build_alembic_config() -> Config:
    bootstrap_environment()
    database_url = os.getenv("DATABASE_URL", "").strip()
    if not database_url:
        raise RuntimeError("DATABASE_URL unavailable after container environment bootstrap")

    config = Config(str(ALEMBIC_INI))
    # Alembic uses ConfigParser interpolation, so literal percent signs in a
    # credential-bearing URL must be doubled when assigned programmatically.
    config.set_main_option("sqlalchemy.url", database_url.replace("%", "%%"))
    return config


def main() -> int:
    command.upgrade(build_alembic_config(), "head")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
