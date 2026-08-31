from __future__ import annotations

import subprocess
from pathlib import Path

import scripts.generate_release_manifest as release_manifest
import scripts.local_source_provenance as provenance
import scripts.package_release as package_release


def _repo(root: Path) -> None:
    subprocess.run(['git', 'init', '-q'], cwd=root, check=True)
    subprocess.run(['git', 'config', 'user.email', 't@example.invalid'], cwd=root, check=True)
    subprocess.run(['git', 'config', 'user.name', 'T'], cwd=root, check=True)
    (root / 'README.md').write_text('committed\n')
    (root / 'reports').mkdir()
    (root / 'reports/PROJECT_STATUS.json').write_text('{}\n')
    subprocess.run(['git', 'add', '.'], cwd=root, check=True)
    subprocess.run(['git', 'commit', '-q', '-m', 'seed'], cwd=root, check=True)


def test_local_source_provenance_detects_dirty_tracked_root_source_file(tmp_path: Path):
    _repo(tmp_path)
    assert provenance.collect(root=tmp_path, source_roots=['README.md'])['clean_tree'] is True
    (tmp_path / 'README.md').write_text('tampered\n')
    result = provenance.collect(root=tmp_path, source_roots=['README.md'])
    assert result['clean_tree'] is False
    assert any('README.md' in row for row in result['dirty_source_entries'])


def test_local_source_provenance_detects_untracked_file_inside_source_scope(tmp_path: Path):
    _repo(tmp_path)
    (tmp_path / 'backend').mkdir()
    (tmp_path / 'backend/new_runtime.py').write_text('x=1\n')
    result = provenance.collect(root=tmp_path, source_roots=['backend'])
    assert result['clean_tree'] is False
    assert any('backend/new_runtime.py' in row for row in result['dirty_source_entries'])


def test_release_source_hash_scope_includes_security_and_provider_contracts():
    required = {
        'README.md', 'SECURITY_MODEL.md', 'DATA_PROVIDER_REGISTRY.yaml',
        'INCIDENT_RUNBOOKS.md', 'SOURCE_RECOVERY_LINEAGE.json',
        'reports/PHASE26_BINANCE_OFFICIAL_API_VERIFICATION.md',
    }
    assert required <= set(release_manifest.SOURCE_ROOTS)


def test_source_package_includes_current_official_exchange_reference():
    assert 'PHASE26_BINANCE_OFFICIAL_API_VERIFICATION.md' in package_release.CANONICAL_REPORT_FILES
