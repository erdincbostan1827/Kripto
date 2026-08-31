from __future__ import annotations

import json
import zipfile
from pathlib import Path

from scripts.package_evidence import build_evidence_archive, verify_evidence_archive
from scripts.package_release import build_release


def test_source_release_excludes_historical_and_external_evidence_reports(tmp_path: Path):
    root=tmp_path/'project'; root.mkdir(); (root/'backend').mkdir(); (root/'backend/app.py').write_text('x=1\n')
    (root/'reports').mkdir(); (root/'reports/LATEST_PYTEST.txt').write_text('ok\n'); (root/'reports/PHASE53_UNIT_A.txt').write_text('historical\n')
    (root/'reports/external_acceptance').mkdir(); (root/'reports/external_acceptance/manifest_all.json').write_text('{}\n')
    archive=tmp_path/'source.zip'; build_release(root=root, archive=archive)
    with zipfile.ZipFile(archive) as zf:
        names=zf.namelist()
        assert any(n.endswith('reports/LATEST_PYTEST.txt') for n in names)
        assert not any('PHASE53_UNIT_A.txt' in n for n in names)
        assert not any('external_acceptance' in n for n in names)


def test_evidence_bundle_is_git_bound_and_hash_verified(tmp_path: Path, monkeypatch):
    root=tmp_path/'project'; root.mkdir(); (root/'reports/external_acceptance').mkdir(parents=True)
    (root/'RELEASE_MANIFEST.json').write_text('{"prod_live_status":"BLOCKED"}\n')
    (root/'reports/external_acceptance/profile.json').write_text('{"status":"BLOCKED"}\n')
    (root/'reports/external_acceptance/manifest_all.json').write_text(json.dumps({"evidence":[],"source_profiles":{"runtime":{"reference":"reports/external_acceptance/profile.json"}}}))
    monkeypatch.setattr('scripts.package_evidence.git_sha', lambda _root: 'a'*40)
    archive=tmp_path/'evidence.zip'; _,manifest=build_evidence_archive(root=root,archive=archive)
    assert manifest['git_commit_sha']=='a'*40
    assert verify_evidence_archive(archive)=={'verified':True,'problems':[]}
    with zipfile.ZipFile(archive) as zf:
        assert 'reports/external_acceptance/profile.json' in zf.namelist()


def test_evidence_bundle_does_not_sweep_unreferenced_logs_or_secrets(tmp_path: Path, monkeypatch):
    root=tmp_path/'project'; root.mkdir(); (root/'reports/external_acceptance').mkdir(parents=True)
    (root/'reports/external_acceptance/manifest_all.json').write_text('{"evidence":[],"source_profiles":{}}')
    (root/'reports/external_acceptance/random.log').write_text('do not sweep')
    (root/'secrets').mkdir(); (root/'secrets/key').write_text('secret')
    monkeypatch.setattr('scripts.package_evidence.git_sha', lambda _root: 'b'*40)
    archive=tmp_path/'evidence.zip'; build_evidence_archive(root=root,archive=archive)
    with zipfile.ZipFile(archive) as zf:
        names=zf.namelist()
        assert not any(n.endswith('random.log') for n in names)
        assert not any('secrets' in Path(n).parts for n in names)
