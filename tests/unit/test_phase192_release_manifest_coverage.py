from __future__ import annotations
import json
from collections import Counter
from pathlib import Path
import pytest
import scripts.generate_release_manifest as release


def _minimal_root(tmp_path: Path) -> Path:
    (tmp_path/'reports').mkdir()
    (tmp_path/'frontend').mkdir()
    (tmp_path/'architecture_profile.yaml').write_text('profile: test\n')
    (tmp_path/'REQUIREMENTS_TRACEABILITY_MATRIX.yaml').write_text('requirements: []\n')
    (tmp_path/'requirements_acceptance_matrix.yaml').write_text('requirements: []\n')
    (tmp_path/'reports/LATEST_PYTEST.txt').write_text('1171 tests collected\n')
    (tmp_path/'reports/LATEST_COVERAGE.txt').write_text('TOTAL 100 10 90%\n')
    (tmp_path/'reports/SBOM.local.json').write_text('{}\n')
    return tmp_path


def test_acceptance_statuses_maps_all_external_groups_to_pass():
    groups={
      'dependency_locks_and_frontend_build':'PASS','runtime':'PASS','restart_drills':'PASS','pitr':'PASS','ha':'PASS','worm':'PASS',
      'testnet':'PASS','private_stream':'PASS','paper_campaign':'PASS','live_shadow':'PASS','profitability':'PASS','supply_chain':'PASS','provenance':'PASS',
    }
    status=release.acceptance_statuses({'groups':groups})
    assert all(v=='PASS' for v in status.values())


def test_known_release_blockers_can_close_local_categories_when_inputs_are_pass():
    acceptance={k:'PASS' for k in release.acceptance_statuses({'groups':{
      'dependency_locks_and_frontend_build':'PASS','runtime':'PASS','restart_drills':'PASS','pitr':'PASS','ha':'PASS','worm':'PASS',
      'testnet':'PASS','private_stream':'PASS','paper_campaign':'PASS','live_shadow':'PASS','profitability':'PASS','supply_chain':'PASS','provenance':'PASS'}})}
    blockers=release.known_release_blockers(acceptance=acceptance,p0_counts=Counter({'PASS':1}),uv_lock_state={'source_compliant':True},frontend_lock_state={'source_compliant':True})
    assert blockers==[]


def test_coverage_truth_accepts_only_git_bound_threshold(monkeypatch: pytest.MonkeyPatch,tmp_path: Path):
    monkeypatch.setattr(release,'ROOT',_minimal_root(tmp_path))
    monkeypatch.setattr(release,'verify_local_coverage',lambda *a,**k:{'verified':True,'status':'PASS','coverage_percent':90.5,'manifest_sha256':'a'*64})
    good=release.coverage_truth(); assert good['fresh'] and good['percent']==90.5 and good['classification']=='FRESH_GIT_BOUND_COVERAGE_EVIDENCE'
    monkeypatch.setattr(release,'verify_local_coverage',lambda *a,**k:{'verified':True,'status':'PASS','coverage_percent':89.99,'manifest_sha256':'b'*64})
    low=release.coverage_truth(); assert not low['fresh'] and low['percent'] is None and 'BELOW_RELEASE_THRESHOLD' in low['blocker']


def test_legacy_coverage_truth_marks_stale_reference_not_fresh(monkeypatch: pytest.MonkeyPatch,tmp_path: Path):
    root=_minimal_root(tmp_path); (root/'reports/LATEST_COVERAGE.txt').write_text('PRIOR VERIFIED REFERENCE\nTOTAL 100 1 99%\n')
    monkeypatch.setattr(release,'ROOT',root)
    monkeypatch.setattr(release,'verify_local_coverage',lambda *a,**k:{'verified':False,'status':'BLOCKED'})
    result=release.coverage_truth(); assert result['fresh'] is False and result['percent'] is None


def test_release_manifest_main_emits_fail_closed_local_manifest(monkeypatch: pytest.MonkeyPatch,tmp_path: Path):
    root=_minimal_root(tmp_path); monkeypatch.setattr(release,'ROOT',root)
    monkeypatch.setattr(release,'external_acceptance_evidence',lambda:{'status':'NOT_TESTED','groups':{},'verified':False,'provenance':None})
    monkeypatch.setattr(release,'verify_local_acceptance',lambda *a,**k:{'status':'PASS','verified':True,'problems':[],'manifest_sha256':'c'*64})
    monkeypatch.setattr(release,'coverage_truth',lambda:{'percent':None,'fresh':False,'classification':'COVERAGE_NOT_FRESH_OR_INCOMPLETE','reference':'reports/local_coverage/full_coverage_manifest.json','sha256':'d'*64})
    monkeypatch.setattr(release,'test_count',lambda:1171)
    monkeypatch.setattr(release,'migration_head',lambda:'m1')
    monkeypatch.setattr(release,'git_sha',lambda:'e'*40)
    monkeypatch.setattr(release,'p0_status_counts',lambda:Counter({'PASS':1469,'NOT_TESTED':42}))
    release.main()
    manifest=json.loads((root/'RELEASE_MANIFEST.json').read_text())
    assert manifest['prod_live_status']=='BLOCKED' and manifest['live_enabled'] is False and manifest['default_mode']=='PAPER'
    assert manifest['git_commit_sha']=='e'*40 and manifest['test_evidence']['test_count']==1171
    assert manifest['test_evidence']['coverage_percent'] is None and manifest['known_release_blockers']
    assert manifest['source_lock_state']['backend']['source_compliant'] is False


def test_test_count_legacy_formats(monkeypatch: pytest.MonkeyPatch,tmp_path: Path):
    root=_minimal_root(tmp_path); monkeypatch.setattr(release,'ROOT',root); monkeypatch.setattr(release,'read_test_inventory',lambda root:{'verified':False})
    p=root/'reports/TEST_COUNT.txt'; p.write_text('123 tests collected\n'); assert release.test_count()==123
    p.write_text('77\n'); assert release.test_count()==77
    p.write_text('tests/a.py: 3\ntests/b.py: 4\n'); assert release.test_count()==7

def test_release_helpers_fail_closed_without_git_alembic_or_matrix(monkeypatch: pytest.MonkeyPatch,tmp_path: Path):
    root=_minimal_root(tmp_path); monkeypatch.setattr(release,'ROOT',root)
    monkeypatch.setattr(release.subprocess,'check_output',lambda *a,**k: (_ for _ in ()).throw(RuntimeError('missing')))
    assert release.git_sha()=='UNAVAILABLE'
    assert release.migration_head()=='UNKNOWN'
    (root/'requirements_acceptance_matrix.yaml').write_text('not: [valid')
    assert release.p0_status_counts()==Counter({'MISSING':1})


def test_p0_status_counts_reads_priorities(monkeypatch: pytest.MonkeyPatch,tmp_path: Path):
    root=_minimal_root(tmp_path); monkeypatch.setattr(release,'ROOT',root)
    (root/'requirements_acceptance_matrix.yaml').write_text('requirements:\n  - priority: P0\n    status: PASS\n  - priority: P0\n    status: NOT_TESTED\n  - priority: P1\n    status: FAIL\n')
    assert release.p0_status_counts()==Counter({'PASS':1,'NOT_TESTED':1})


def test_test_count_missing_evidence_is_none(monkeypatch: pytest.MonkeyPatch,tmp_path: Path):
    root=_minimal_root(tmp_path); monkeypatch.setattr(release,'ROOT',root); monkeypatch.setattr(release,'read_test_inventory',lambda root:{'verified':False})
    (root/'reports/TEST_COUNT.txt').unlink(missing_ok=True)
    assert release.test_count() is None
