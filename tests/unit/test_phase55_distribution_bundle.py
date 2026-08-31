from __future__ import annotations
import json
from pathlib import Path
from scripts.package_distribution import validate_release_binding


def _write(root:Path,release:dict,prov:dict):
    (root/'reports').mkdir(parents=True,exist_ok=True)
    release.setdefault('test_evidence', {
      'test_count': 1, 'coverage_percent': None, 'coverage_fresh': False,
      'coverage_classification': 'COVERAGE_NOT_FRESH_OR_INCOMPLETE',
    })
    (root/'RELEASE_MANIFEST.json').write_text(json.dumps(release))
    (root/'reports/LOCAL_SOURCE_PROVENANCE.json').write_text(json.dumps(prov))
    (root/'reports/TEST_COUNT.txt').write_text('1 tests collected\n')
    (root/'reports/PROJECT_STATUS.json').write_text(json.dumps({
      'test_count': 1, 'backend_coverage_percent': None, 'coverage_fresh': False,
      'coverage_classification': 'COVERAGE_NOT_FRESH_OR_INCOMPLETE',
      'default_mode': release.get('default_mode'), 'live_enabled': release.get('live_enabled'),
      'prod_live_status': release.get('prod_live_status','BLOCKED'),
    }))


def test_distribution_binding_requires_same_git_sha_clean_tagged_paper_live_off(tmp_path:Path):
    sha='a'*40
    _write(tmp_path,
      {'git_commit_sha':sha,'default_mode':'PAPER','live_enabled':False,'prod_live_status':'BLOCKED'},
      {'git_commit_sha':sha,'clean_tree':True,'immutable_tag_present':True})
    r=validate_release_binding(tmp_path,expected_git_sha=sha)
    assert r['verified'] is True and r['problems']==[]


def test_distribution_binding_rejects_stale_release_or_provenance(tmp_path:Path):
    sha='a'*40; old='b'*40
    _write(tmp_path,
      {'git_commit_sha':old,'default_mode':'PAPER','live_enabled':False},
      {'git_commit_sha':old,'clean_tree':True,'immutable_tag_present':True})
    r=validate_release_binding(tmp_path,expected_git_sha=sha)
    assert r['verified'] is False
    assert 'RELEASE_MANIFEST_GIT_MISMATCH' in r['problems'] and 'SOURCE_PROVENANCE_GIT_MISMATCH' in r['problems']


def test_distribution_binding_rejects_live_enabled_or_non_paper_default(tmp_path:Path):
    sha='c'*40
    _write(tmp_path,
      {'git_commit_sha':sha,'default_mode':'LIVE','live_enabled':True},
      {'git_commit_sha':sha,'clean_tree':True,'immutable_tag_present':True})
    r=validate_release_binding(tmp_path,expected_git_sha=sha)
    assert 'DEFAULT_MODE_NOT_PAPER' in r['problems'] and 'LIVE_NOT_DISABLED' in r['problems']
