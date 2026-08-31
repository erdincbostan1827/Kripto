from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from datetime import datetime, timezone

import pytest

import scripts.database_backup_receipt as backup_receipt
import scripts.database_migration_guard as guard
import scripts.operation_lock as oplock
import scripts.transactional_release_update as update


def _release(root: Path, head: str = "m1") -> Path:
    root.mkdir(parents=True, exist_ok=True)
    (root / "marker.txt").write_text("x")
    versions = root / "alembic" / "versions"; versions.mkdir(parents=True)
    (versions / "0001.py").write_text(f"revision = {head!r}\ndown_revision = None\n")
    (root / guard.CONTRACT_FILE).write_text(json.dumps({"schema_version":"1.0","classification":"DATABASE_MIGRATION_COMPATIBILITY_CONTRACT","migrations":{head:{"down_revision":None,"previous_release_compatible":True,"requires_backup":True,"rollback_strategy":"restore_or_forward"}}}))
    return root


def _restore_receipt(path: Path, backup_hash: str, *, tables: int = 2) -> Path:
    body={"schema_version":"1.1","classification":"VERIFIED_DATABASE_RESTORE_DRILL_RECEIPT","backup_sha256":backup_hash,"restore_status":"PASS","restored_table_count":tables,"environment_id":"test-env","environment_fingerprint":guard._environment_fingerprint("test-env"),"completed_at":datetime.now(timezone.utc).isoformat(),"policy":"REAL_RESTORE_COMMAND_COMPLETED_AND_DATABASE_SMOKE_CHECK_PASSED; ENVIRONMENT_BOUND_AND_FRESHNESS_VERIFIABLE"}
    body["provenance_sha256"]=guard._canonical_hash(body); path.write_text(json.dumps(body)); return path


def test_operation_lock_rejects_second_writer_and_preserves_owner(tmp_path: Path):
    with oplock.operation_lock(tmp_path, operation="release-update") as first:
        with pytest.raises(RuntimeError, match="OPERATION_LOCK_BUSY"):
            with oplock.operation_lock(tmp_path, operation="release-rollback"):
                pass
        payload=json.loads((tmp_path/oplock.LOCK_NAME).read_text())
        assert payload["token"] == first["token"] and payload["operation"] == "release-update"
    assert not (tmp_path/oplock.LOCK_NAME).exists()


def test_stale_lock_recovery_requires_dead_owner_and_age(tmp_path: Path):
    dead_pid = 99999999
    payload={"schema_version":"1.0","classification":"PLATFORM_OPERATION_LOCK","token":"dead","operation":"release-update","pid":dead_pid,"hostname":"test","created_at":"test","created_epoch":time.time()-120,"policy":"x"}
    (tmp_path/oplock.LOCK_NAME).write_text(json.dumps(payload))
    out=oplock.recover_stale_lock(tmp_path, minimum_age_seconds=30)
    assert out["recovered"] is True and not (tmp_path/oplock.LOCK_NAME).exists()


def test_live_owner_lock_cannot_be_stolen(tmp_path: Path):
    payload={"schema_version":"1.0","classification":"PLATFORM_OPERATION_LOCK","token":"live","operation":"database-migration","pid":os.getpid(),"hostname":"test","created_at":"test","created_epoch":time.time()-999,"policy":"x"}
    (tmp_path/oplock.LOCK_NAME).write_text(json.dumps(payload))
    with pytest.raises(RuntimeError, match="OWNER_STILL_ALIVE"):
        oplock.recover_stale_lock(tmp_path, minimum_age_seconds=1)
    assert (tmp_path/oplock.LOCK_NAME).exists()


def test_restore_drill_receipt_tamper_fails_closed(tmp_path: Path):
    backup=tmp_path/'db.dump'; backup.write_bytes(b'abc'); digest=hashlib.sha256(backup.read_bytes()).hexdigest()
    receipt=_restore_receipt(tmp_path/'restore.json',digest)
    assert guard.verify_restore_drill_receipt(receipt, expected_backup_sha256=digest)["verified"] is True
    body=json.loads(receipt.read_text()); body["restored_table_count"]=99; receipt.write_text(json.dumps(body))
    with pytest.raises(RuntimeError, match="PROVENANCE_MISMATCH"):
        guard.verify_restore_drill_receipt(receipt, expected_backup_sha256=digest)


def test_backup_receipt_cannot_be_created_without_matching_restore_drill(tmp_path: Path):
    active=_release(tmp_path/'active'); backup=tmp_path/'db.dump'; backup.write_bytes(b'abc')
    restore=_restore_receipt(tmp_path/'restore.json','f'*64)
    with pytest.raises(RuntimeError, match="RESTORE_DRILL_BACKUP_HASH_MISMATCH"):
        backup_receipt.create_receipt(backup=backup,restore_drill_receipt=restore,active=active,migration_head='m1',environment_id='test-env',output=tmp_path/'backup-receipt.json')


def test_backup_receipt_binds_restore_drill_hash_and_provenance(tmp_path: Path):
    active=_release(tmp_path/'active'); backup=tmp_path/'db.dump'; backup.write_bytes(b'abc'); digest=hashlib.sha256(backup.read_bytes()).hexdigest()
    restore=_restore_receipt(tmp_path/'restore.json',digest)
    out=tmp_path/'backup-receipt.json'; result=backup_receipt.create_receipt(backup=backup,restore_drill_receipt=restore,active=active,migration_head='m1',environment_id='test-env',output=out)
    verified=guard.verify_backup_receipt(out,expected_head='m1',expected_active_tree_sha256=update._tree_sha256(active))
    assert result["created"] and verified["restore_drill_receipt_sha256"] == hashlib.sha256(restore.read_bytes()).hexdigest()
    restore.write_text(restore.read_text()+"\n")
    with pytest.raises(RuntimeError, match="RECEIPT_HASH_MISMATCH"):
        guard.verify_backup_receipt(out,expected_head='m1',expected_active_tree_sha256=update._tree_sha256(active))


def test_release_update_is_blocked_by_existing_platform_operation_lock(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    active=_release(tmp_path/'active'); package=tmp_path/'x.zip'; package.write_bytes(b'x')
    with oplock.operation_lock(tmp_path, operation="database-migration"):
        with pytest.raises(RuntimeError, match="OPERATION_LOCK_BUSY"):
            update.apply_update(package=package, active=active)
    assert (active/'marker.txt').read_text() == 'x'


def test_database_migration_is_blocked_by_update_lock_before_probe(tmp_path: Path):
    active=_release(tmp_path/'active'); candidate=_release(tmp_path/'candidate','m2'); state=tmp_path/'state'; backup=tmp_path/'none.json'
    with oplock.operation_lock(tmp_path, operation="release-update"):
        with pytest.raises(RuntimeError, match="OPERATION_LOCK_BUSY"):
            guard.run_guarded_migration(active=active,candidate=candidate,state_dir=state,backup_receipt=backup,probe_command=[sys.executable,'-c','raise SystemExit(99)'],migration_command=[sys.executable,'-c','raise SystemExit(99)'])


def test_lock_file_symlink_is_fail_closed(tmp_path: Path):
    target=tmp_path/'target'; target.write_text('{}'); (tmp_path/oplock.LOCK_NAME).symlink_to(target)
    with pytest.raises(RuntimeError, match="OPERATION_LOCK_UNSAFE"):
        with oplock.operation_lock(tmp_path, operation='release-update'):
            pass


def test_install_scripts_are_guarded_by_same_platform_operation_mutex():
    root=Path(__file__).resolve().parents[2]
    linux=(root/'install.sh').read_text(); windows=(root/'INSTALL_WINDOWS.ps1').read_text()
    for text in (linux,windows):
        assert 'operation_lock_exec.py' in text
        assert '--operation install' in text
        assert 'CTP_INSTALL_LOCK_HELD' in text
