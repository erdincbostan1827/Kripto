from __future__ import annotations

import argparse
import os
import stat
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _regular_file_no_symlink(path: Path, *, error: str) -> os.stat_result:
    st = path.lstat()
    if stat.S_ISLNK(st.st_mode) or not stat.S_ISREG(st.st_mode):
        raise RuntimeError(error)
    return st


def bootstrap_env(*, root: Path = ROOT) -> dict:
    template = root / ".env.example"
    target = root / ".env"
    if not template.exists():
        raise RuntimeError("ENV_TEMPLATE_MISSING")
    template_st = _regular_file_no_symlink(template, error="ENV_TEMPLATE_UNSAFE")
    if template_st.st_size <= 0:
        raise RuntimeError("ENV_TEMPLATE_EMPTY")

    if target.exists() or target.is_symlink():
        st = _regular_file_no_symlink(target, error="ENV_TARGET_UNSAFE")
        if st.st_size <= 0:
            raise RuntimeError("ENV_TARGET_EMPTY")
        target.chmod(0o600)
        return {"classification": "ENV_BOOTSTRAP", "status": "KEPT_EXISTING", "created": False}

    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        fd = os.open(target, flags, 0o600)
    except FileExistsError:
        st = _regular_file_no_symlink(target, error="ENV_TARGET_UNSAFE")
        if st.st_size <= 0:
            raise RuntimeError("ENV_TARGET_EMPTY")
        target.chmod(0o600)
        return {"classification": "ENV_BOOTSTRAP", "status": "KEPT_EXISTING", "created": False}

    try:
        with template.open("rb") as src:
            while True:
                chunk = src.read(1024 * 1024)
                if not chunk:
                    break
                view = memoryview(chunk)
                while view:
                    count = os.write(fd, view)
                    if count <= 0:
                        raise OSError("ENV_WRITE_INCOMPLETE")
                    view = view[count:]
        os.fsync(fd)
    except BaseException:
        try:
            os.close(fd)
        finally:
            try:
                target.unlink()
            except FileNotFoundError:
                pass
        raise
    else:
        os.close(fd)
        target.chmod(0o600)
        return {"classification": "ENV_BOOTSTRAP", "status": "CREATED", "created": True}


def main() -> int:
    parser = argparse.ArgumentParser(description="Create .env once from .env.example without following symlinks.")
    parser.parse_args()
    result = bootstrap_env()
    print(f"ENV_{result['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
