from __future__ import annotations

import base64
import os
import secrets
import stat
from pathlib import Path


SECRET_NAMES = (
    "postgres_password.txt",
    "grafana_admin_password.txt",
    "audit_hmac_key.txt",
    "heartbeat_hmac_key.txt",
    "app_encryption_key.txt",
    "admin_bootstrap_token.txt",
    "backup_encryption_key.txt",
)


def token(nbytes: int = 32) -> str:
    return secrets.token_urlsafe(nbytes)


def fernet_key() -> str:
    return base64.urlsafe_b64encode(secrets.token_bytes(32)).decode("ascii")


def _validate_secret_dir(root: Path) -> None:
    if root.exists():
        st = root.lstat()
        if stat.S_ISLNK(st.st_mode) or not stat.S_ISDIR(st.st_mode):
            raise RuntimeError("SECRETS_DIRECTORY_UNSAFE")
        root.chmod(0o700)
        return
    root.mkdir(mode=0o700, parents=False, exist_ok=False)


def _validate_existing_secret(path: Path) -> None:
    st = path.lstat()
    if stat.S_ISLNK(st.st_mode) or not stat.S_ISREG(st.st_mode):
        raise RuntimeError(f"SECRET_PATH_UNSAFE:{path.name}")
    if st.st_size <= 0:
        raise RuntimeError(f"SECRET_EMPTY:{path.name}")
    path.chmod(0o600)


def write_secret_once(root: Path, name: str, value: str) -> bool:
    if name not in SECRET_NAMES or Path(name).name != name:
        raise ValueError("SECRET_NAME_INVALID")
    if not value:
        raise ValueError("SECRET_VALUE_EMPTY")
    _validate_secret_dir(root)
    path = root / name
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        fd = os.open(path, flags, 0o600)
    except FileExistsError:
        _validate_existing_secret(path)
        return False
    try:
        data = value.encode("utf-8")
        written = 0
        while written < len(data):
            count = os.write(fd, data[written:])
            if count <= 0:
                raise OSError("SECRET_WRITE_INCOMPLETE")
            written += count
        os.fsync(fd)
    except BaseException:
        try:
            os.close(fd)
        finally:
            try:
                path.unlink()
            except FileNotFoundError:
                pass
        raise
    else:
        os.close(fd)
        path.chmod(0o600)
        return True


def bootstrap(root: Path = Path("secrets")) -> dict[str, str]:
    values = {
        "postgres_password.txt": token(32),
        "grafana_admin_password.txt": token(32),
        "audit_hmac_key.txt": token(48),
        "heartbeat_hmac_key.txt": token(48),
        "app_encryption_key.txt": fernet_key(),
        "admin_bootstrap_token.txt": token(32),
        "backup_encryption_key.txt": fernet_key(),
    }
    results: dict[str, str] = {}
    for name, value in values.items():
        created = write_secret_once(root, name, value)
        results[name] = "created" if created else "kept-existing"
    return results


def main() -> None:
    results = bootstrap()
    for name, status in results.items():
        print(f"{status} secrets/{name}")


if __name__ == "__main__":
    main()
