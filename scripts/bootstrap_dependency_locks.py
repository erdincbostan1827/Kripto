from __future__ import annotations

import argparse
import json
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.acceptance_diagnostics import classify_blocker, redact_text

REPORT = ROOT / "reports" / "dependency_lock_bootstrap.json"
TRANSACTION_JOURNAL = ".dependency-lock-bootstrap.transaction.json"
TRANSACTION_PREFIX = ".lock-bootstrap-txn-"
TARGETS = {"uv": Path("uv.lock"), "npm": Path("frontend/package-lock.json")}
LOCK_RESOLUTION_TIMEOUT_SECONDS = 600
PROCESS_TREE_GRACE_SECONDS = 2.0


def _digest(path: Path) -> str | None:
    return sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def _atomic_write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2, sort_keys=True)
            fh.write("\n")
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(temp_name, path)
    except BaseException:
        try:
            os.unlink(temp_name)
        except FileNotFoundError:
            pass
        raise


def _terminate_process_tree(proc: subprocess.Popen[str]) -> None:
    """Terminate the resolver and descendants so a timeout cannot orphan npm/uv workers."""
    if proc.poll() is not None:
        return
    try:
        if os.name == "posix":
            os.killpg(proc.pid, signal.SIGTERM)
        elif os.name == "nt":
            subprocess.run(
                ["taskkill", "/PID", str(proc.pid), "/T", "/F"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=5,
                check=False,
            )
        else:
            proc.terminate()
    except (ProcessLookupError, OSError, subprocess.SubprocessError):
        try:
            proc.terminate()
        except (ProcessLookupError, OSError):
            pass

    deadline = time.monotonic() + PROCESS_TREE_GRACE_SECONDS
    while proc.poll() is None and time.monotonic() < deadline:
        time.sleep(0.05)
    if proc.poll() is not None:
        return
    try:
        if os.name == "posix":
            os.killpg(proc.pid, signal.SIGKILL)
        else:
            proc.kill()
    except (ProcessLookupError, OSError):
        pass


def _run(cmd: list[str], cwd: Path, *, offline: bool) -> dict:
    env = os.environ.copy()
    if offline:
        if cmd[0] == "uv":
            cmd = [*cmd, "--offline"]
        elif cmd[0] == "npm":
            cmd = [*cmd, "--offline"]
    tool = shutil.which(cmd[0])
    if tool is None:
        return {"command": cmd, "exit_code": None, "ok": False, "blocker": f"TOOL_UNAVAILABLE:{cmd[0]}", "output": ""}

    popen_kwargs: dict = {
        "cwd": cwd,
        "env": env,
        "text": True,
        "stdout": subprocess.PIPE,
        "stderr": subprocess.STDOUT,
    }
    if os.name == "posix":
        popen_kwargs["start_new_session"] = True
    elif os.name == "nt":
        popen_kwargs["creationflags"] = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)

    proc = subprocess.Popen(cmd, **popen_kwargs)
    try:
        output, _ = proc.communicate(timeout=LOCK_RESOLUTION_TIMEOUT_SECONDS)
    except subprocess.TimeoutExpired as exc:
        partial = exc.output or ""
        if isinstance(partial, bytes):
            partial = partial.decode(errors="replace")
        _terminate_process_tree(proc)
        try:
            final_output, _ = proc.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            try:
                proc.kill()
            except (ProcessLookupError, OSError):
                pass
            final_output, _ = proc.communicate()
        output = final_output or partial
        safe_output = redact_text(output)[-8000:]
        return {
            "command": cmd,
            "exit_code": None,
            "ok": False,
            "blocker": "COMMAND_OR_NETWORK_TIMEOUT",
            "output": safe_output,
            "process_tree_terminated": proc.poll() is not None,
        }

    output = output or ""
    return {
        "command": cmd,
        "exit_code": proc.returncode,
        "ok": proc.returncode == 0,
        "blocker": None if proc.returncode == 0 else classify_blocker(output, proc.returncode, tool=cmd[0]),
        "output": redact_text(output)[-8000:],
        "process_tree_terminated": False,
    }


def _journal_path(root: Path) -> Path:
    return root / TRANSACTION_JOURNAL


def _validate_transaction_dir(root: Path, raw: object) -> Path:
    if not isinstance(raw, str) or not raw:
        raise RuntimeError("LOCK_TRANSACTION_DIR_INVALID")
    candidate = Path(raw)
    if not candidate.is_absolute():
        candidate = root / candidate
    resolved_root = root.resolve()
    resolved = candidate.resolve(strict=False)
    if resolved.parent != resolved_root or not resolved.name.startswith(TRANSACTION_PREFIX):
        raise RuntimeError("LOCK_TRANSACTION_DIR_OUTSIDE_ROOT")
    if candidate.is_symlink():
        raise RuntimeError("LOCK_TRANSACTION_DIR_SYMLINK")
    if not candidate.is_dir():
        raise RuntimeError("LOCK_TRANSACTION_DIR_MISSING")
    return candidate


def _backup_path(tx_dir: Path, key: str) -> Path:
    return tx_dir / "backups" / ("uv.lock" if key == "uv" else "package-lock.json")


def _candidate_path(tx_dir: Path, key: str) -> Path:
    return tx_dir / "candidates" / ("uv.lock" if key == "uv" else "package-lock.json")


def _restore_copy(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{target.name}.restore-", dir=target.parent)
    os.close(fd)
    temp = Path(temp_name)
    try:
        shutil.copy2(source, temp)
        os.replace(temp, target)
    finally:
        try:
            temp.unlink()
        except FileNotFoundError:
            pass


def _restore_pre_transaction_state(root: Path, tx_dir: Path, journal: dict) -> None:
    before = journal.get("before")
    if not isinstance(before, dict) or set(before) != set(TARGETS):
        raise RuntimeError("LOCK_TRANSACTION_BEFORE_STATE_INVALID")
    for key, rel in TARGETS.items():
        row = before.get(key)
        if not isinstance(row, dict) or not isinstance(row.get("present"), bool):
            raise RuntimeError(f"LOCK_TRANSACTION_BEFORE_ROW_INVALID:{key}")
        target = root / rel
        if row["present"]:
            backup = _backup_path(tx_dir, key)
            expected = row.get("sha256")
            if not backup.is_file() or not isinstance(expected, str) or _digest(backup) != expected:
                raise RuntimeError(f"LOCK_TRANSACTION_BACKUP_INVALID:{key}")
            _restore_copy(backup, target)
        else:
            if target.exists() and not target.is_file():
                raise RuntimeError(f"LOCK_TRANSACTION_TARGET_TYPE_INVALID:{key}")
            target.unlink(missing_ok=True)

    for key, rel in TARGETS.items():
        row = before[key]
        target = root / rel
        if row["present"]:
            if _digest(target) != row["sha256"]:
                raise RuntimeError(f"LOCK_TRANSACTION_ROLLBACK_VERIFY_FAILED:{key}")
        elif target.exists():
            raise RuntimeError(f"LOCK_TRANSACTION_ROLLBACK_ABSENCE_FAILED:{key}")


def recover_incomplete_transaction(root: Path = ROOT) -> dict:
    journal_path = _journal_path(root)
    if not journal_path.exists():
        return {"recovered": False, "status": "NO_TRANSACTION"}
    if not journal_path.is_file() or journal_path.is_symlink():
        raise RuntimeError("LOCK_TRANSACTION_JOURNAL_INVALID_TYPE")
    try:
        journal = json.loads(journal_path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise RuntimeError(f"LOCK_TRANSACTION_JOURNAL_INVALID:{type(exc).__name__}") from exc
    if journal.get("schema_version") != "1.0" or journal.get("classification") != "DEPENDENCY_LOCK_PROMOTION_TRANSACTION":
        raise RuntimeError("LOCK_TRANSACTION_JOURNAL_CONTRACT_INVALID")
    tx_dir = _validate_transaction_dir(root, journal.get("transaction_dir"))
    _restore_pre_transaction_state(root, tx_dir, journal)
    journal_path.unlink()
    shutil.rmtree(tx_dir, ignore_errors=True)
    return {"recovered": True, "status": "ROLLED_BACK_INTERRUPTED_TRANSACTION"}


def _promote_file(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    os.replace(source, target)


def _prepare_transaction(root: Path, tx_dir: Path, before: dict[str, str | None], candidates: dict[str, Path]) -> dict:
    backup_dir = tx_dir / "backups"
    candidate_dir = tx_dir / "candidates"
    backup_dir.mkdir(parents=True, exist_ok=True)
    candidate_dir.mkdir(parents=True, exist_ok=True)

    before_rows: dict[str, dict] = {}
    candidate_rows: dict[str, dict] = {}
    for key, rel in TARGETS.items():
        target = root / rel
        previous = before[key]
        before_rows[key] = {"present": previous is not None, "sha256": previous}
        if previous is not None:
            backup = _backup_path(tx_dir, key)
            shutil.copy2(target, backup)
            if _digest(backup) != previous:
                raise RuntimeError(f"LOCK_TRANSACTION_BACKUP_VERIFY_FAILED:{key}")
        stable_candidate = _candidate_path(tx_dir, key)
        shutil.copy2(candidates[key], stable_candidate)
        digest = _digest(stable_candidate)
        if digest is None:
            raise RuntimeError(f"LOCK_TRANSACTION_CANDIDATE_MISSING:{key}")
        candidate_rows[key] = {"sha256": digest}

    journal = {
        "schema_version": "1.0",
        "classification": "DEPENDENCY_LOCK_PROMOTION_TRANSACTION",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": "PREPARED",
        "transaction_dir": tx_dir.name,
        "before": before_rows,
        "candidates": candidate_rows,
        "policy": "ROLL_BACK_TO_PRE_TRANSACTION_STATE_ON_INTERRUPTION",
    }
    _atomic_write_json(_journal_path(root), journal)
    return journal


def _update_journal(root: Path, journal: dict, status: str) -> dict:
    updated = {**journal, "status": status, "updated_at": datetime.now(timezone.utc).isoformat()}
    _atomic_write_json(_journal_path(root), updated)
    return updated


def _commit_transaction(root: Path, tx_dir: Path, journal: dict) -> None:
    current = journal
    for key, rel in TARGETS.items():
        candidate = _candidate_path(tx_dir, key)
        expected = journal["candidates"][key]["sha256"]
        if _digest(candidate) != expected:
            raise RuntimeError(f"LOCK_TRANSACTION_CANDIDATE_CHANGED:{key}")
        _promote_file(candidate, root / rel)
        current = _update_journal(root, current, f"PROMOTED_{key.upper()}")

    for key, rel in TARGETS.items():
        if _digest(root / rel) != journal["candidates"][key]["sha256"]:
            raise RuntimeError(f"LOCK_TRANSACTION_COMMIT_VERIFY_FAILED:{key}")
    _update_journal(root, current, "VERIFIED_BOTH")
    _journal_path(root).unlink()


def bootstrap(*, root: Path = ROOT, offline: bool = False) -> dict:
    recovery = recover_incomplete_transaction(root)
    targets = {k: root / rel for k, rel in TARGETS.items()}
    before = {k: _digest(v) for k, v in targets.items()}
    tx_dir = Path(tempfile.mkdtemp(prefix=TRANSACTION_PREFIX, dir=root))
    results: dict[str, dict] = {}
    committed = False
    rollback = {"attempted": False, "succeeded": None}
    try:
        work = tx_dir / "work"
        py_dir = work / "python"
        js_dir = work / "frontend"
        py_dir.mkdir(parents=True)
        js_dir.mkdir(parents=True)
        shutil.copy2(root / "pyproject.toml", py_dir / "pyproject.toml")
        shutil.copy2(root / "frontend" / "package.json", js_dir / "package.json")

        results["uv"] = _run(["uv", "lock"], py_dir, offline=offline)
        uv_candidate = py_dir / "uv.lock"
        results["uv"]["candidate_present"] = uv_candidate.is_file()

        results["npm"] = _run(["npm", "install", "--package-lock-only", "--ignore-scripts"], js_dir, offline=offline)
        npm_candidate = js_dir / "package-lock.json"
        results["npm"]["candidate_present"] = npm_candidate.is_file()

        all_ok = results["uv"]["ok"] and uv_candidate.is_file() and results["npm"]["ok"] and npm_candidate.is_file()
        if all_ok:
            journal = _prepare_transaction(root, tx_dir, before, {"uv": uv_candidate, "npm": npm_candidate})
            try:
                _commit_transaction(root, tx_dir, journal)
                committed = True
            except Exception:
                rollback["attempted"] = True
                try:
                    _restore_pre_transaction_state(root, tx_dir, journal)
                    _journal_path(root).unlink(missing_ok=True)
                    rollback["succeeded"] = True
                except Exception as rollback_exc:
                    rollback["succeeded"] = False
                    rollback["error"] = type(rollback_exc).__name__
                raise

        after = {k: _digest(v) for k, v in targets.items()}
        return {
            "schema_version": "1.1",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "classification": "DEPENDENCY_LOCK_BOOTSTRAP_RESULT",
            "offline": offline,
            "committed": committed,
            "atomic_policy": "BOTH_OR_NONE",
            "atomic_mechanism": "DURABLE_ROLLBACK_JOURNAL",
            "recovery": recovery,
            "rollback": rollback,
            "before_sha256": before,
            "after_sha256": after,
            "results": results,
            "truth_policy": "Lock files are committed only when both ecosystems resolve and both promoted files verify. Interrupted or failed promotion is rolled back from a durable transaction journal before another bootstrap may proceed.",
        }
    finally:
        # Keep recovery material if a hard interruption or failed rollback left an authoritative journal.
        if not _journal_path(root).exists():
            shutil.rmtree(tx_dir, ignore_errors=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--offline", action="store_true", help="Resolve only from local caches; never use registries.")
    parser.add_argument("--recover-only", action="store_true", help="Recover an interrupted promotion without resolving dependencies.")
    parser.add_argument("--report", type=Path, default=REPORT)
    args = parser.parse_args()
    try:
        if args.recover_only:
            recovery = recover_incomplete_transaction(ROOT)
            payload = {
                "schema_version": "1.1",
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "classification": "DEPENDENCY_LOCK_RECOVERY_RESULT",
                "recovery": recovery,
                "committed": False,
            }
            exit_code = 0
        else:
            payload = bootstrap(offline=args.offline)
            exit_code = 0 if payload["committed"] else 2
    except Exception as exc:
        payload = {
            "schema_version": "1.1",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "classification": "DEPENDENCY_LOCK_BOOTSTRAP_FAIL_CLOSED",
            "committed": False,
            "error": type(exc).__name__,
            "message": redact_text(str(exc))[:1000],
        }
        exit_code = 2
    _atomic_write_json(args.report, payload)
    print(json.dumps({"committed": payload.get("committed", False), "report": str(args.report), "classification": payload["classification"]}, sort_keys=True))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
