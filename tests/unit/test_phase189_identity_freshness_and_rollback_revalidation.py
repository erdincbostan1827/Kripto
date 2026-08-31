from __future__ import annotations

import hashlib
import json
import os
import socket
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

import scripts.database_backup_receipt as backup_receipt
import scripts.database_migration_guard as guard
import scripts.operation_lock as oplock
import scripts.transactional_release_update as update


def _release(root: Path, revisions: list[tuple[str, str | None]], marker: str) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    (root / "marker.txt").write_text(marker)
    versions = root / "alembic" / "versions"; versions.mkdir(parents=True)
    entries = {}
    for i, (rev, down) in enumerate(revisions):
        (versions / f"{i:04d}_{rev}.py").write_text(f"revision = {rev!r}\ndown_revision = {down!r}\n" if down else f"revision = {rev!r}\ndown_revision = None\n")
        entries[rev] = {"down_revision": down, "previous_release_compatible": True, "requires_backup": True, "rollback_strategy": "restore_or_forward"}
    (root / guard.CONTRACT_FILE).write_text(json.dumps({"schema_version":"1.0","classification":"DATABASE_MIGRATION_COMPATIBILITY_CONTRACT","migrations":entries}))
    return root


def _restore_receipt(path: Path, backup_hash: str, env: str, *, age_seconds: int = 0) -> Path:
    body = {
        "schema_version":"1.1", "classification":"VERIFIED_DATABASE_RESTORE_DRILL_RECEIPT",
        "backup_sha256":backup_hash, "restore_status":"PASS", "restored_table_count":3,
        "environment_id":env, "environment_fingerprint":guard._environment_fingerprint(env),
        "completed_at":(datetime.now(timezone.utc)-timedelta(seconds=age_seconds)).isoformat(),
        "policy":"REAL_RESTORE_COMMAND_COMPLETED_AND_DATABASE_SMOKE_CHECK_PASSED; ENVIRONMENT_BOUND_AND_FRESHNESS_VERIFIABLE",
    }
    body["provenance_sha256"] = guard._canonical_hash(body)
    path.write_text(json.dumps(body)); return path


def test_new_operation_lock_binds_boot_and_process_start_identity(tmp_path: Path):
    with oplock.operation_lock(tmp_path, operation="release-update") as held:
        payload=json.loads((tmp_path/oplock.LOCK_NAME).read_text())
        assert payload["schema_version"] == "1.1"
        assert payload["boot_identity"] == held["boot_identity"]
        assert payload["process_start_identity"] == held["process_start_identity"]
        assert payload["process_start_identity"] == oplock._process_start_identity(os.getpid())


def test_pid_reuse_is_treated_as_stale_not_live_owner(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(oplock, "_boot_identity", lambda: "boot-x")
    monkeypatch.setattr(oplock, "_process_start_identity", lambda pid: "new-process")
    monkeypatch.setattr(oplock, "_pid_alive", lambda pid: True)
    payload={"schema_version":"1.1","classification":"PLATFORM_OPERATION_LOCK","token":"old","operation":"release-update","pid":123,"hostname":socket.gethostname(),"boot_identity":"boot-x","process_start_identity":"old-process","created_at":"x","created_epoch":time.time()-120,"policy":"x"}
    (tmp_path/oplock.LOCK_NAME).write_text(json.dumps(payload))
    result=oplock.recover_stale_lock(tmp_path, minimum_age_seconds=30)
    assert result["recovered"] is True and result["owner_state"] == "PID_REUSED"


def test_remote_host_lock_is_never_stolen_from_shared_storage(tmp_path: Path):
    payload={"schema_version":"1.1","classification":"PLATFORM_OPERATION_LOCK","token":"remote","operation":"release-update","pid":99999999,"hostname":"other-host","boot_identity":"boot","process_start_identity":"proc","created_at":"x","created_epoch":time.time()-999,"policy":"x"}
    (tmp_path/oplock.LOCK_NAME).write_text(json.dumps(payload))
    with pytest.raises(RuntimeError, match="REMOTE_UNVERIFIABLE"):
        oplock.recover_stale_lock(tmp_path, minimum_age_seconds=1)
    assert (tmp_path/oplock.LOCK_NAME).exists()


def test_real_subprocess_second_writer_is_rejected(tmp_path: Path):
    root=Path(__file__).resolve().parents[2]
    ready=tmp_path/"ready"
    code=("import time; from pathlib import Path; from scripts.operation_lock import operation_lock; "
          f"p=Path({str(tmp_path)!r}); r=Path({str(ready)!r}); "
          "\nwith operation_lock(p, operation='holder'):\n r.write_text('ready')\n time.sleep(20)\n")
    proc=subprocess.Popen([sys.executable,"-c",code], cwd=root)
    try:
        for _ in range(100):
            if ready.exists(): break
            if proc.poll() is not None: raise AssertionError(f"holder exited {proc.returncode}")
            time.sleep(0.05)
        assert ready.exists()
        with pytest.raises(RuntimeError, match="OPERATION_LOCK_BUSY"):
            with oplock.operation_lock(tmp_path, operation="contender"):
                pass
    finally:
        proc.terminate()
        try: proc.wait(timeout=5)
        except subprocess.TimeoutExpired: proc.kill(); proc.wait(timeout=5)
    # A hard-terminated writer leaves the lock behind; recovery proves the
    # recorded owner identity is no longer the original live process.
    recovered=oplock.recover_stale_lock(tmp_path, minimum_age_seconds=0)
    assert recovered["recovered"] is True and recovered["owner_state"] in {"DEAD", "PID_REUSED"}


def test_restore_receipt_is_environment_bound_and_freshness_enforced(tmp_path: Path):
    backup=tmp_path/"db.dump"; backup.write_bytes(b"abc"); digest=hashlib.sha256(backup.read_bytes()).hexdigest()
    receipt=_restore_receipt(tmp_path/"restore.json", digest, "prod-a")
    assert guard.verify_restore_drill_receipt(receipt, expected_backup_sha256=digest, expected_environment_id="prod-a")["verified"]
    with pytest.raises(RuntimeError, match="ENVIRONMENT_MISMATCH"):
        guard.verify_restore_drill_receipt(receipt, expected_backup_sha256=digest, expected_environment_id="prod-b")
    stale=_restore_receipt(tmp_path/"stale.json", digest, "prod-a", age_seconds=90000)
    with pytest.raises(RuntimeError, match="RECEIPT_STALE"):
        guard.verify_restore_drill_receipt(stale, expected_backup_sha256=digest, expected_environment_id="prod-a")


def test_backup_receipt_binds_actual_environment_and_fresh_restore(tmp_path: Path):
    active=_release(tmp_path/"active", [("m1",None)], "old")
    backup=tmp_path/"db.dump"; backup.write_bytes(b"abc"); digest=hashlib.sha256(backup.read_bytes()).hexdigest()
    restore=_restore_receipt(tmp_path/"restore.json", digest, "prod-a")
    out=tmp_path/"backup.json"
    backup_receipt.create_receipt(backup=backup, restore_drill_receipt=restore, active=active, migration_head="m1", environment_id="prod-a", output=out)
    verified=guard.verify_backup_receipt(out, expected_head="m1", expected_active_tree_sha256=update._tree_sha256(active), expected_environment_id="prod-a")
    assert verified["environment_fingerprint"] == guard._environment_fingerprint("prod-a")
    with pytest.raises(RuntimeError, match="ENVIRONMENT_MISMATCH"):
        guard.verify_backup_receipt(out, expected_head="m1", expected_active_tree_sha256=update._tree_sha256(active), expected_environment_id="prod-b")


def test_migrated_release_rollback_requires_db_probe_and_revalidates_compatibility(tmp_path: Path):
    rollback=_release(tmp_path/(update.BACKUP_PREFIX+"x"), [("m1",None)], "old")
    active=_release(tmp_path/"active", [("m1",None),("m2","m1")], "new")
    pre_hash=update._tree_sha256(rollback); post_hash=update._tree_sha256(active)
    acceptance=update._write_acceptance_receipt(parent=tmp_path, token="x", pre_tree_sha256=pre_hash, post_tree_sha256=post_hash, post_identity={"git_commit_sha":"f"*40}, binding={"migration_version":"m2","architecture_profile_hash":"a"*64}, migration_receipt_verification={"receipt_sha256":"b"*64,"provenance_sha256":"c"*64})
    update._write_rollback_receipt(backup=rollback, pre_hash=pre_hash, post_identity={"git_commit_sha":"f"*40}, binding={"migration_version":"m2"}, acceptance_receipt=acceptance)
    with pytest.raises(RuntimeError, match="ROLLBACK_DATABASE_COMPATIBILITY_PROBE_REQUIRED"):
        update.rollback_last_update(active=active, rollback_dir=rollback)
    probe=[sys.executable,"-c","print('m2')"]
    result=update.rollback_last_update(active=active, rollback_dir=rollback, database_probe_command=probe)
    assert result["rolled_back"] is True
    assert result["database_compatibility"]["status"] == "NEW_SCHEMA_VERIFIED_COMPATIBLE_WITH_ROLLBACK_CODE"
    assert (active/"marker.txt").read_text() == "old"


def test_migrated_release_rollback_rejects_ambiguous_database_head(tmp_path: Path):
    rollback=_release(tmp_path/(update.BACKUP_PREFIX+"y"), [("m1",None)], "old")
    active=_release(tmp_path/"active", [("m1",None),("m2","m1")], "new")
    pre_hash=update._tree_sha256(rollback)
    acceptance=update._write_acceptance_receipt(parent=tmp_path, token="y", pre_tree_sha256=pre_hash, post_tree_sha256=update._tree_sha256(active), post_identity={"git_commit_sha":"f"*40}, binding={"migration_version":"m2","architecture_profile_hash":"a"*64}, migration_receipt_verification={"receipt_sha256":"b"*64,"provenance_sha256":"c"*64})
    update._write_rollback_receipt(backup=rollback, pre_hash=pre_hash, post_identity={"git_commit_sha":"f"*40}, binding={"migration_version":"m2"}, acceptance_receipt=acceptance)
    with pytest.raises(RuntimeError, match="ROLLBACK_DATABASE_HEAD_AMBIGUOUS"):
        update.rollback_last_update(active=active, rollback_dir=rollback, database_probe_command=[sys.executable,"-c","print('mystery')"])
    assert (active/"marker.txt").read_text() == "new"
