from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

import scripts.bootstrap_env as env_bootstrap
import scripts.transactional_release_update as update


def _migration_fixture(root: Path, head: str = "m1") -> None:
    versions = root / "alembic" / "versions"; versions.mkdir(parents=True, exist_ok=True)
    (versions / "001.py").write_text(f"revision = '{head}'\ndown_revision = None\n")
    (root / "MIGRATION_COMPATIBILITY.json").write_text(json.dumps({
        "schema_version": "1.0", "classification": "DATABASE_MIGRATION_COMPATIBILITY_CONTRACT",
        "migrations": {head: {"down_revision": None, "previous_release_compatible": True, "requires_backup": True, "rollback_strategy": "restore_or_forward"}}
    }))


def test_env_bootstrap_create_once_preserves_existing(tmp_path: Path):
    (tmp_path / '.env.example').write_text('MODE=PAPER\n', encoding='utf-8')
    first = env_bootstrap.bootstrap_env(root=tmp_path)
    assert first['created'] is True
    assert (tmp_path / '.env').read_text() == 'MODE=PAPER\n'
    (tmp_path / '.env').write_text('MODE=TESTNET\n', encoding='utf-8')
    second = env_bootstrap.bootstrap_env(root=tmp_path)
    assert second['created'] is False
    assert (tmp_path / '.env').read_text() == 'MODE=TESTNET\n'


def test_env_bootstrap_rejects_symlink_target(tmp_path: Path):
    (tmp_path / '.env.example').write_text('MODE=PAPER\n')
    outside = tmp_path / 'outside'; outside.write_text('SECRET=keep\n')
    try:
        (tmp_path / '.env').symlink_to(outside)
    except OSError:
        pytest.skip('symlinks unavailable')
    with pytest.raises(RuntimeError, match='ENV_TARGET_UNSAFE'):
        env_bootstrap.bootstrap_env(root=tmp_path)
    assert outside.read_text() == 'SECRET=keep\n'


def test_env_bootstrap_failed_write_removes_partial_target(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    (tmp_path / '.env.example').write_text('MODE=PAPER\n')
    original_write = env_bootstrap.os.write
    calls = {'n': 0}
    def fail_after_create(fd, data):
        calls['n'] += 1
        if calls['n'] == 1:
            return original_write(fd, data[:1])
        raise OSError('simulated env write failure')
    monkeypatch.setattr(env_bootstrap.os, 'write', fail_after_create)
    with pytest.raises(OSError, match='simulated env write failure'):
        env_bootstrap.bootstrap_env(root=tmp_path)
    assert not (tmp_path / '.env').exists()


def _active_tree(parent: Path, name: str = 'active') -> Path:
    active = parent / name; active.mkdir(); (active / 'marker.txt').write_text('old'); _migration_fixture(active)
    return active


def _fake_extract(package: Path, destination: Path, **kwargs):
    project = destination / 'project'; project.mkdir(); (project / 'marker.txt').write_text('new'); _migration_fixture(project)
    return {'classification': 'SOURCE_PACKAGE_SAFE_EXTRACTION'}


def _verified(root: Path):
    return {'verified': True, 'problems': []}


def test_release_update_cutover_retains_verified_rollback_tree(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    active = _active_tree(tmp_path); package = tmp_path / 'source.zip'; package.write_bytes(b'x')
    monkeypatch.setattr(update, 'extract', _fake_extract)
    monkeypatch.setattr(update, 'verify_source_package_identity', _verified)
    monkeypatch.setattr(update, 'run_post_cutover_acceptance', lambda root, **kwargs: {'accepted': True, 'problems': [], 'binding': {'accepted': True, 'problems': []}})
    result = update.apply_update(package=package, active=active)
    rollback = Path(result['rollback_directory'])
    assert (active / 'marker.txt').read_text() == 'new'
    assert (rollback / 'marker.txt').read_text() == 'old'
    assert not (tmp_path / update.JOURNAL).exists()


def test_interrupted_cutover_rolls_back_original_active_tree(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    active = _active_tree(tmp_path); package = tmp_path / 'source.zip'; package.write_bytes(b'x')
    monkeypatch.setattr(update, 'extract', _fake_extract)
    monkeypatch.setattr(update, 'verify_source_package_identity', _verified)
    monkeypatch.setattr(update, 'run_post_cutover_acceptance', lambda root, **kwargs: {'accepted': True, 'problems': [], 'binding': {'accepted': True, 'problems': []}})
    original_replace = update.os.replace
    calls = {'candidate_promote': 0}
    def flaky_replace(src, dst):
        srcp, dstp = Path(src), Path(dst)
        if srcp.name.startswith(update.CANDIDATE_PREFIX) and dstp.name == 'active':
            calls['candidate_promote'] += 1
            raise OSError('simulated cutover failure')
        return original_replace(src, dst)
    monkeypatch.setattr(update.os, 'replace', flaky_replace)
    with pytest.raises(OSError, match='simulated cutover failure'):
        update.apply_update(package=package, active=active)
    assert (active / 'marker.txt').read_text() == 'old'
    assert not (tmp_path / update.JOURNAL).exists()


def test_recover_surviving_post_promotion_journal_prefers_old_tree(tmp_path: Path):
    active = _active_tree(tmp_path)
    active.rename(tmp_path / f'{update.BACKUP_PREFIX}abc')
    backup = tmp_path / f'{update.BACKUP_PREFIX}abc'
    active.mkdir(); (active / 'marker.txt').write_text('new')
    candidate = tmp_path / f'{update.CANDIDATE_PREFIX}abc'; candidate.mkdir(); (candidate / 'x').write_text('x')
    journal = {
        'schema_version': '1.0', 'classification': 'RELEASE_UPDATE_TRANSACTION',
        'active_name': 'active', 'backup': backup.name, 'candidate': candidate.name,
        'status': 'CANDIDATE_PROMOTED'
    }
    (tmp_path / update.JOURNAL).write_text(json.dumps(journal))
    result = update.recover_incomplete_update(active=active)
    assert result['recovered'] is True
    assert (active / 'marker.txt').read_text() == 'old'
    assert not candidate.exists()


def test_recovery_rejects_redirected_backup_path(tmp_path: Path):
    active = _active_tree(tmp_path)
    journal = {
        'schema_version': '1.0', 'classification': 'RELEASE_UPDATE_TRANSACTION',
        'active_name': 'active', 'backup': '../outside', 'candidate': f'{update.CANDIDATE_PREFIX}abc',
        'status': 'ACTIVE_MOVED_TO_BACKUP'
    }
    (tmp_path / update.JOURNAL).write_text(json.dumps(journal))
    with pytest.raises(RuntimeError, match='OUTSIDE_PARENT'):
        update.recover_incomplete_update(active=active)


def test_explicit_rollback_restores_previous_tree(tmp_path: Path):
    active = _active_tree(tmp_path)
    (active / 'marker.txt').write_text('new')
    backup = tmp_path / f'{update.BACKUP_PREFIX}abc'; backup.mkdir(); (backup / 'marker.txt').write_text('old')
    acceptance = tmp_path / f'{update.ACCEPTANCE_PREFIX}abc.json'
    body = {'schema_version': '1.0', 'classification': 'VERIFIED_RELEASE_UPDATE_ACCEPTANCE_RECEIPT', 'transaction_id': 'abc'}
    body['provenance_sha256'] = update._canonical_hash(body); update._atomic_json(acceptance, body)
    update._atomic_json(update._receipt_path(backup), {
        'schema_version': '1.0', 'classification': 'VERIFIED_RELEASE_ROLLBACK_RECEIPT',
        'backup': backup.name, 'backup_tree_sha256': update._tree_sha256(backup),
        'acceptance_receipt': acceptance.name, 'acceptance_receipt_sha256': update._sha256_file(acceptance),
    })
    result = update.rollback_last_update(active=active, rollback_dir=backup)
    assert result['rolled_back'] is True
    assert (active / 'marker.txt').read_text() == 'old'
    assert not backup.exists()


def test_installers_use_safe_env_bootstrap_before_secret_bootstrap():
    root = Path(__file__).resolve().parents[2]
    for path in (root / 'install.sh', root / 'INSTALL_WINDOWS.ps1'):
        text = path.read_text(encoding='utf-8')
        assert 'bootstrap_env.py' in text
        assert text.index('bootstrap_env.py') < text.index('bootstrap_secrets.py')
        assert 'Copy-Item .env.example .env' not in text
        assert 'cp .env.example .env' not in text
