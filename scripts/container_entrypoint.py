from __future__ import annotations
import hashlib
import os
from pathlib import Path


def read_file_env(name: str) -> str | None:
    direct = os.getenv(name)
    if direct:
        return direct
    path = os.getenv(f"{name}_FILE")
    if not path:
        return None
    value = Path(path).read_text(encoding="utf-8").strip()
    if not value:
        raise RuntimeError(f"{name}_FILE is empty")
    return value


def bootstrap_environment() -> None:
    password = read_file_env("POSTGRES_PASSWORD")
    if not os.getenv("DATABASE_URL") and password:
        os.environ["DATABASE_URL"] = f"postgresql+psycopg://trading:{password}@postgres:5432/trading"
    for name in ("AUDIT_HMAC_KEY", "HEARTBEAT_HMAC_KEY", "APP_ENCRYPTION_KEY"):
        value = read_file_env(name)
        if value:
            os.environ[name] = value
    bootstrap = read_file_env("ADMIN_BOOTSTRAP_TOKEN")
    if bootstrap and not os.getenv("ADMIN_BOOTSTRAP_TOKEN_HASH"):
        os.environ["ADMIN_BOOTSTRAP_TOKEN_HASH"] = hashlib.sha256(bootstrap.encode()).hexdigest()


def main() -> None:
    bootstrap_environment()
    from uvicorn import run
    # The container must listen on every interface so its published port is reachable.
    run("app.main:app", app_dir="/app/backend", host="0.0.0.0", port=8000, proxy_headers=True, forwarded_allow_ips="127.0.0.1")  # nosec B104

if __name__ == "__main__":
    main()
