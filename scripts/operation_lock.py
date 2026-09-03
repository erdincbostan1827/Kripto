from __future__ import annotations

import json
import math
import os
import socket
import time
import uuid
import threading
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

LOCK_NAME = ".platform-operation.lock.json"
SCHEMA_VERSION = "1.1"
DEFAULT_HEARTBEAT_INTERVAL_SECONDS = 5.0
_PROCESS_INSTANCE_ID = uuid.uuid4().hex


def _atomic_create_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    fd = os.open(path, flags, 0o600)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2, sort_keys=True)
            fh.write("\n")
            fh.flush()
            os.fsync(fh.fileno())
    except BaseException:
        try:
            path.unlink()
        except FileNotFoundError:
            pass
        raise


def _atomic_replace_json(path: Path, payload: dict) -> None:
    if path.is_symlink() or not path.is_file():
        raise RuntimeError("OPERATION_LOCK_UNSAFE")
    tmp = path.parent / f".{path.name}.{uuid.uuid4().hex}.tmp"
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    fd = os.open(tmp, flags, 0o600)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2, sort_keys=True)
            fh.write("\n")
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, path)
    except BaseException:
        try:
            tmp.unlink()
        except FileNotFoundError:
            pass
        raise


def _next_heartbeat_epoch(current: dict) -> float:
    try:
        created_epoch = float(current["created_epoch"])
        previous_epoch = float(current.get("heartbeat_epoch", created_epoch))
    except (KeyError, TypeError, ValueError, OverflowError) as exc:
        raise RuntimeError("OPERATION_LOCK_HEARTBEAT_EPOCH_INVALID") from exc
    if (
        not math.isfinite(created_epoch)
        or not math.isfinite(previous_epoch)
        or previous_epoch < created_epoch
    ):
        raise RuntimeError("OPERATION_LOCK_HEARTBEAT_EPOCH_INVALID")
    observed_epoch = time.time()
    if not math.isfinite(observed_epoch):
        raise RuntimeError("OPERATION_LOCK_CLOCK_INVALID")
    next_epoch = max(observed_epoch, math.nextafter(previous_epoch, math.inf))
    if not math.isfinite(next_epoch):
        raise RuntimeError("OPERATION_LOCK_HEARTBEAT_EPOCH_EXHAUSTED")
    return next_epoch


def _refresh_heartbeat(path: Path, *, token: str, boot_identity: str, process_start_identity: str) -> float:
    current = _read_lock(path)
    if current.get("token") != token:
        raise RuntimeError("OPERATION_LOCK_OWNERSHIP_LOST")
    if current.get("boot_identity") != boot_identity or current.get("process_start_identity") != process_start_identity:
        raise RuntimeError("OPERATION_LOCK_OWNER_IDENTITY_CHANGED")
    now = _next_heartbeat_epoch(current)
    updated = dict(current)
    updated["heartbeat_epoch"] = now
    updated["heartbeat_at"] = datetime.now(timezone.utc).isoformat()
    _atomic_replace_json(path, updated)
    return now


def _boot_identity() -> str | None:
    """Return a boot-stable local identity without inventing one when unavailable."""
    linux = Path("/proc/sys/kernel/random/boot_id")
    try:
        value = linux.read_text(encoding="utf-8").strip()
        if value:
            return f"linux-boot-id:{value}"
    except OSError:
        pass
    try:
        import psutil  # type: ignore

        return f"psutil-boot-time:{psutil.boot_time():.6f}"
    except Exception:
        return None


def _process_start_identity(pid: int) -> str | None:
    """Return a value that changes when a PID is reused."""
    try:
        import psutil  # type: ignore

        return f"psutil-create-time:{psutil.Process(pid).create_time():.6f}"
    except Exception:
        pass
    stat = Path(f"/proc/{pid}/stat")
    try:
        text = stat.read_text(encoding="utf-8")
        # /proc/<pid>/stat field 22 is the process start time in clock ticks.
        tail = text.rsplit(")", 1)[1].strip().split()
        if len(tail) >= 20:
            return f"proc-start-ticks:{tail[19]}"
    except OSError:
        pass
    # Sandboxed runtimes may intentionally hide /proc and deny psutil's
    # create_time probe.  A per-interpreter nonce still provides an
    # unambiguous identity for locks owned by this process. Other processes
    # remain unverifiable (fail closed) unless their OS identity is readable.
    if pid == os.getpid():
        return f"process-instance:{_PROCESS_INSTANCE_ID}"
    return None


def _read_lock(path: Path) -> dict:
    if path.is_symlink() or not path.is_file():
        raise RuntimeError("OPERATION_LOCK_UNSAFE")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise RuntimeError(f"OPERATION_LOCK_INVALID:{type(exc).__name__}") from exc
    if payload.get("schema_version") not in {"1.0", SCHEMA_VERSION} or payload.get("classification") != "PLATFORM_OPERATION_LOCK":
        raise RuntimeError("OPERATION_LOCK_CONTRACT_INVALID")
    if not isinstance(payload.get("token"), str) or not payload["token"]:
        raise RuntimeError("OPERATION_LOCK_TOKEN_INVALID")
    if not isinstance(payload.get("pid"), int) or payload["pid"] <= 0:
        raise RuntimeError("OPERATION_LOCK_PID_INVALID")
    if payload.get("schema_version") == SCHEMA_VERSION:
        for key in ("hostname", "boot_identity", "process_start_identity"):
            if not isinstance(payload.get(key), str) or not payload[key]:
                raise RuntimeError(f"OPERATION_LOCK_{key.upper()}_INVALID")
    return payload


def _pid_alive(pid: int) -> bool:
    if pid == os.getpid():
        return True
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return True
    return True


def _owner_state(payload: dict) -> str:
    """Classify owner without treating a reused PID as the original process."""
    pid = payload["pid"]
    if payload.get("schema_version") == "1.0":
        return "ALIVE" if _pid_alive(pid) else "DEAD_LEGACY"
    if payload.get("hostname") != socket.gethostname():
        # Shared storage may surface a lock from another host. We cannot safely
        # prove that owner dead from this host, therefore never steal it.
        return "REMOTE_UNVERIFIABLE"
    current_boot = _boot_identity()
    if current_boot is None:
        return "BOOT_IDENTITY_UNVERIFIABLE"
    if payload.get("boot_identity") != current_boot:
        return "PRIOR_BOOT"
    if not _pid_alive(pid):
        return "DEAD"
    current_start = _process_start_identity(pid)
    if current_start is None:
        return "PROCESS_IDENTITY_UNVERIFIABLE"
    if current_start != payload.get("process_start_identity"):
        return "PID_REUSED"
    return "ALIVE"


def recover_stale_lock(lock_dir: Path, *, minimum_age_seconds: int = 30) -> dict:
    lock_dir = lock_dir.resolve()
    path = lock_dir / LOCK_NAME
    if not path.exists() and not path.is_symlink():
        return {"recovered": False, "status": "NO_LOCK"}
    payload = _read_lock(path)
    state = _owner_state(payload)
    if state == "ALIVE":
        raise RuntimeError("OPERATION_LOCK_OWNER_STILL_ALIVE")
    if state in {"REMOTE_UNVERIFIABLE", "BOOT_IDENTITY_UNVERIFIABLE", "PROCESS_IDENTITY_UNVERIFIABLE"}:
        raise RuntimeError(f"OPERATION_LOCK_OWNER_{state}")
    try:
        created_epoch = float(payload["created_epoch"])
        lease_epoch = float(payload.get("heartbeat_epoch", created_epoch))
    except Exception as exc:
        raise RuntimeError("OPERATION_LOCK_CREATED_EPOCH_INVALID") from exc
    if lease_epoch < created_epoch:
        raise RuntimeError("OPERATION_LOCK_HEARTBEAT_EPOCH_INVALID")
    age = time.time() - lease_epoch
    if age < minimum_age_seconds:
        raise RuntimeError("OPERATION_LOCK_STALE_AGE_NOT_REACHED")
    # Re-read immediately before unlink to reduce TOCTOU risk and require token
    # continuity. Never delete a replacement lock owned by another process.
    current = _read_lock(path)
    if current.get("token") != payload.get("token"):
        raise RuntimeError("OPERATION_LOCK_STALE_RECOVERY_OWNERSHIP_CHANGED")
    path.unlink()
    return {
        "recovered": True,
        "status": "STALE_LOCK_REMOVED",
        "token": payload["token"],
        "age_seconds": age,
        "owner_state": state,
    }


@contextmanager
def operation_lock(
    lock_dir: Path,
    *,
    operation: str,
    recover_stale: bool = False,
    minimum_stale_age_seconds: int = 30,
    heartbeat_interval_seconds: float = DEFAULT_HEARTBEAT_INTERVAL_SECONDS,
):
    lock_dir = lock_dir.resolve()
    if lock_dir.is_symlink() or not lock_dir.is_dir():
        raise RuntimeError("OPERATION_LOCK_DIRECTORY_UNSAFE")
    if heartbeat_interval_seconds <= 0 or heartbeat_interval_seconds > 300:
        raise RuntimeError("OPERATION_LOCK_HEARTBEAT_INTERVAL_INVALID")
    boot_identity = _boot_identity()
    process_start_identity = _process_start_identity(os.getpid())
    if boot_identity is None or process_start_identity is None:
        raise RuntimeError("OPERATION_LOCK_OWNER_IDENTITY_UNAVAILABLE")
    path = lock_dir / LOCK_NAME
    if recover_stale and (path.exists() or path.is_symlink()):
        recover_stale_lock(lock_dir, minimum_age_seconds=minimum_stale_age_seconds)
    token = uuid.uuid4().hex
    now = time.time()
    payload = {
        "schema_version": SCHEMA_VERSION,
        "classification": "PLATFORM_OPERATION_LOCK",
        "token": token,
        "operation": operation,
        "pid": os.getpid(),
        "hostname": socket.gethostname(),
        "boot_identity": boot_identity,
        "process_start_identity": process_start_identity,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_epoch": now,
        "heartbeat_at": datetime.now(timezone.utc).isoformat(),
        "heartbeat_epoch": now,
        "policy": "SINGLE_WRITER_FAIL_CLOSED; PID_REUSE_AND_CROSS_BOOT_SAFE_STALE_RECOVERY; HEARTBEAT_LEASE_REFRESH",
    }
    try:
        _atomic_create_json(path, payload)
    except FileExistsError as exc:
        existing = _read_lock(path)
        raise RuntimeError(f"OPERATION_LOCK_BUSY:{existing.get('operation')}:{existing.get('pid')}") from exc

    stop = threading.Event()
    heartbeat_errors: list[BaseException] = []
    heartbeat_refresh_lock = threading.Lock()

    def _refresh_owned_heartbeat() -> float:
        with heartbeat_refresh_lock:
            return _refresh_heartbeat(
                path,
                token=token,
                boot_identity=boot_identity,
                process_start_identity=process_start_identity,
            )

    def _heartbeat_worker() -> None:
        while not stop.wait(heartbeat_interval_seconds):
            try:
                _refresh_owned_heartbeat()
            except BaseException as exc:
                heartbeat_errors.append(exc)
                stop.set()
                return

    thread = threading.Thread(target=_heartbeat_worker, name=f"platform-lock-heartbeat-{operation}", daemon=True)
    thread.start()
    body_error: BaseException | None = None

    def _assert_healthy() -> None:
        if heartbeat_errors:
            exc = heartbeat_errors[0]
            raise RuntimeError(f"OPERATION_LOCK_HEARTBEAT_FAILED:{type(exc).__name__}:{exc}")
        current = _read_lock(path)
        if current.get("token") != token:
            raise RuntimeError("OPERATION_LOCK_OWNERSHIP_LOST")
        if current.get("boot_identity") != boot_identity or current.get("process_start_identity") != process_start_identity:
            raise RuntimeError("OPERATION_LOCK_OWNER_IDENTITY_CHANGED")

    try:
        yield {
            "token": token, "path": str(path), "operation": operation,
            "boot_identity": boot_identity, "process_start_identity": process_start_identity,
            "heartbeat_interval_seconds": heartbeat_interval_seconds,
            "heartbeat": _refresh_owned_heartbeat,
            "assert_healthy": _assert_healthy,
        }
    except BaseException as exc:
        body_error = exc
        raise
    finally:
        stop.set()
        thread.join(timeout=max(1.0, heartbeat_interval_seconds * 2))
        if thread.is_alive() and body_error is None:
            raise RuntimeError("OPERATION_LOCK_HEARTBEAT_THREAD_DID_NOT_STOP")
        if heartbeat_errors and body_error is None:
            raise RuntimeError(f"OPERATION_LOCK_HEARTBEAT_FAILED:{type(heartbeat_errors[0]).__name__}:{heartbeat_errors[0]}")
        if body_error is None:
            try:
                current = _read_lock(path)
            except FileNotFoundError as exc:
                raise RuntimeError("OPERATION_LOCK_DISAPPEARED") from exc
            if current.get("token") != token:
                raise RuntimeError("OPERATION_LOCK_OWNERSHIP_LOST")
            if current.get("process_start_identity") != process_start_identity or current.get("boot_identity") != boot_identity:
                raise RuntimeError("OPERATION_LOCK_OWNER_IDENTITY_CHANGED")
            path.unlink()
        else:
            # Never suppress the body exception. If ownership is still ours,
            # remove the lock; otherwise preserve the replacement/tampered lock
            # as evidence and let the original failure propagate.
            try:
                current = _read_lock(path)
            except (FileNotFoundError, RuntimeError):
                current = None
            if current is not None and current.get("token") == token and current.get("process_start_identity") == process_start_identity and current.get("boot_identity") == boot_identity:
                path.unlink()
