from __future__ import annotations
import hashlib, json, os, sys, time
from pathlib import Path
import pytest
import scripts.operation_lock as oplock
import scripts.transactional_release_update as update
import scripts.release_provenance_graph as graph


def _tree(root: Path, marker: str) -> Path:
    root.mkdir(parents=True,exist_ok=True); (root/'marker.txt').write_text(marker); return root


def _rollback_fixture(tmp_path: Path):
    rollback=_tree(tmp_path/(update.BACKUP_PREFIX+'x'),'old')
    active=_tree(tmp_path/'active','new')
    pre=update._tree_sha256(rollback)
    acceptance=update._write_acceptance_receipt(parent=tmp_path,token='x',pre_tree_sha256=pre,post_tree_sha256=update._tree_sha256(active),post_identity={'git_commit_sha':'f'*40},binding={'migration_version':'m1','architecture_profile_hash':'a'*64},migration_receipt_verification=None)
    receipt=update._write_rollback_receipt(backup=rollback,pre_hash=pre,post_identity={'git_commit_sha':'f'*40},binding={'migration_version':'m1'},acceptance_receipt=acceptance)
    return active,rollback,acceptance,receipt


def test_operation_lock_heartbeat_advances_lease_epoch(tmp_path: Path):
    with oplock.operation_lock(tmp_path,operation='long-op',heartbeat_interval_seconds=0.05) as held:
        first=json.loads((tmp_path/oplock.LOCK_NAME).read_text())['heartbeat_epoch']
        deadline=time.monotonic()+1.0
        second=first
        while second <= first and time.monotonic() < deadline:
            time.sleep(0.01)
            second=json.loads((tmp_path/oplock.LOCK_NAME).read_text())['heartbeat_epoch']
        assert second > first
        manual=held['heartbeat']()
        assert manual > second
    assert not (tmp_path/oplock.LOCK_NAME).exists()


def test_operation_lock_manual_heartbeat_advances_with_constant_wall_clock(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    fixed_epoch=1_700_000_000.0
    monkeypatch.setattr(oplock.time,'time',lambda:fixed_epoch)
    with oplock.operation_lock(tmp_path,operation='constant-clock',heartbeat_interval_seconds=300) as held:
        path=tmp_path/oplock.LOCK_NAME
        first=json.loads(path.read_text())['heartbeat_epoch']
        manual=held['heartbeat']()
        second=json.loads(path.read_text())['heartbeat_epoch']
        assert first == fixed_epoch
        assert manual == second
        assert second > first
    assert not (tmp_path/oplock.LOCK_NAME).exists()


def test_stale_recovery_uses_heartbeat_not_only_created_epoch(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(oplock,'_boot_identity',lambda:'boot')
    monkeypatch.setattr(oplock,'_process_start_identity',lambda pid:'new')
    monkeypatch.setattr(oplock,'_pid_alive',lambda pid:True)
    now=time.time()
    payload={'schema_version':'1.1','classification':'PLATFORM_OPERATION_LOCK','token':'t','operation':'x','pid':123,'hostname':__import__('socket').gethostname(),'boot_identity':'boot','process_start_identity':'old','created_at':'x','created_epoch':now-1000,'heartbeat_epoch':now-2,'heartbeat_at':'x','policy':'x'}
    (tmp_path/oplock.LOCK_NAME).write_text(json.dumps(payload))
    with pytest.raises(RuntimeError,match='STALE_AGE_NOT_REACHED'):
        oplock.recover_stale_lock(tmp_path,minimum_age_seconds=30)
    assert (tmp_path/oplock.LOCK_NAME).exists()


def test_failed_post_rollback_runtime_acceptance_restores_new_release_and_preserves_evidence(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    active,rollback,acceptance,receipt=_rollback_fixture(tmp_path)
    monkeypatch.setattr(update,'run_post_cutover_acceptance',lambda *a,**k:{'accepted':False,'problems':['health failed']})
    with pytest.raises(RuntimeError,match='ROLLBACK_POST_CUTOVER_ACCEPTANCE_FAILED'):
        update.rollback_last_update(active=active,rollback_dir=rollback,rollback_acceptance_command=[sys.executable,'-c','raise SystemExit(1)'])
    assert (active/'marker.txt').read_text()=='new'
    assert rollback.is_dir() and (rollback/'marker.txt').read_text()=='old'
    assert receipt.is_file() and acceptance.is_file()


def test_successful_post_rollback_runtime_acceptance_commits_and_cleans_evidence(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    active,rollback,acceptance,receipt=_rollback_fixture(tmp_path)
    monkeypatch.setattr(update,'run_post_cutover_acceptance',lambda *a,**k:{'accepted':True,'problems':[],'runtime_command':{'returncode':0}})
    result=update.rollback_last_update(active=active,rollback_dir=rollback,rollback_acceptance_command=[sys.executable,'-c','raise SystemExit(0)'])
    assert result['rolled_back'] and result['post_rollback_acceptance']['accepted']
    assert (active/'marker.txt').read_text()=='old'
    assert not rollback.exists() and not receipt.exists() and not acceptance.exists()


def _write(path: Path,payload: dict)->Path:
    path.write_text(json.dumps(payload,sort_keys=True)); return path


def test_provenance_graph_closes_restore_migration_release_rollback_chain(tmp_path: Path):
    restore_body={'classification':'VERIFIED_DATABASE_RESTORE_DRILL_RECEIPT','provenance_sha256':'r'*64,'environment_fingerprint':'e'*64}
    restore=_write(tmp_path/'restore.json',restore_body); restore_sha=hashlib.sha256(restore.read_bytes()).hexdigest()
    backup_body={'classification':'VERIFIED_DATABASE_BACKUP_RECEIPT','restore_drill_receipt_sha256':restore_sha,'restore_drill_provenance_sha256':'r'*64,'environment_fingerprint':'e'*64,'backup_sha256':'b'*64}
    backup=_write(tmp_path/'backup.json',backup_body); backup_sha=hashlib.sha256(backup.read_bytes()).hexdigest()
    migration_body={'classification':'VERIFIED_DATABASE_MIGRATION_RECEIPT','database_backup_receipt_sha256':backup_sha,'database_restore_drill_receipt_sha256':restore_sha,'database_restore_drill_provenance_sha256':'r'*64,'database_environment_fingerprint':'e'*64,'provenance_sha256':'m'*64}
    migration=_write(tmp_path/'migration.json',migration_body); migration_sha=hashlib.sha256(migration.read_bytes()).hexdigest()
    acceptance_body={'classification':'VERIFIED_RELEASE_UPDATE_ACCEPTANCE_RECEIPT','post_update_git_commit_sha':'a'*40,'migration_receipt_sha256':migration_sha}
    acceptance=_write(tmp_path/'acceptance.json',acceptance_body); acceptance_sha=hashlib.sha256(acceptance.read_bytes()).hexdigest()
    rollback=_write(tmp_path/'rollback.json',{'classification':'VERIFIED_RELEASE_ROLLBACK_RECEIPT','acceptance_receipt_sha256':acceptance_sha})
    provenance=_write(tmp_path/'package.json',{'classification':'PACKAGE_PROVENANCE','git_commit_sha':'a'*40})
    out=tmp_path/'graph.json'
    result=graph.build_graph(acceptance=acceptance,rollback=rollback,migration=migration,backup=backup,restore=restore,package_provenance=provenance,output=out)
    assert result['verified'] and result['node_count']==6 and result['edge_count']==6
    verified=graph.verify_graph(out)
    assert verified['verified_structure'] is True and verified['trusted_provenance'] is False


def test_provenance_graph_rejects_tampered_restore_link(tmp_path: Path):
    restore=_write(tmp_path/'restore.json',{'classification':'VERIFIED_DATABASE_RESTORE_DRILL_RECEIPT','provenance_sha256':'r'*64,'environment_fingerprint':'e'*64}); rs=hashlib.sha256(restore.read_bytes()).hexdigest()
    backup=_write(tmp_path/'backup.json',{'classification':'VERIFIED_DATABASE_BACKUP_RECEIPT','restore_drill_receipt_sha256':'0'*64,'restore_drill_provenance_sha256':'r'*64,'environment_fingerprint':'e'*64,'backup_sha256':'b'*64}); bs=hashlib.sha256(backup.read_bytes()).hexdigest()
    migration=_write(tmp_path/'migration.json',{'classification':'VERIFIED_DATABASE_MIGRATION_RECEIPT','database_backup_receipt_sha256':bs,'database_restore_drill_receipt_sha256':rs,'database_restore_drill_provenance_sha256':'r'*64,'database_environment_fingerprint':'e'*64}); ms=hashlib.sha256(migration.read_bytes()).hexdigest()
    acceptance=_write(tmp_path/'acceptance.json',{'classification':'VERIFIED_RELEASE_UPDATE_ACCEPTANCE_RECEIPT','post_update_git_commit_sha':'a'*40,'migration_receipt_sha256':ms}); acs=hashlib.sha256(acceptance.read_bytes()).hexdigest()
    rollback=_write(tmp_path/'rollback.json',{'classification':'VERIFIED_RELEASE_ROLLBACK_RECEIPT','acceptance_receipt_sha256':acs})
    with pytest.raises(RuntimeError,match='BACKUP_RESTORE_HASH_MISMATCH'):
        graph.build_graph(acceptance=acceptance,rollback=rollback,migration=migration,backup=backup,restore=restore,output=tmp_path/'g.json')
