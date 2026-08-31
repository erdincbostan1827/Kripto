from __future__ import annotations

import hashlib
import json
from pathlib import Path

import scripts.package_evidence as pkg
import scripts.package_release as srcpkg


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_evidence_package_follows_complete_coverage_reference_graph(tmp_path: Path):
    base=tmp_path/'reports/local_coverage'; base.mkdir(parents=True)
    log=base/'coverage_shard_00_of_01.log'; log.write_text('pass')
    data=base/'.coverage.00_of_01'; data.write_bytes(b'coverage-data')
    shard=base/'coverage_shard_00_of_01.json'
    shard.write_text(json.dumps({
      'log':'reports/local_coverage/coverage_shard_00_of_01.log','log_sha256':_sha(log),
      'coverage_data':'reports/local_coverage/.coverage.00_of_01','coverage_data_sha256':_sha(data),
    }))
    cov=base/'coverage.json'; cov.write_text('{}')
    full=base/'full_coverage_manifest.json'
    full.write_text(json.dumps({
      'coverage_json':'reports/local_coverage/coverage.json','coverage_json_sha256':_sha(cov),
      'shards':[{'manifest':'reports/local_coverage/coverage_shard_00_of_01.json','manifest_sha256':_sha(shard)}],
    }))
    refs=pkg._local_coverage_referenced_files(tmp_path)
    assert refs == {
      'reports/local_coverage/full_coverage_manifest.json','reports/local_coverage/coverage.json',
      'reports/local_coverage/coverage_shard_00_of_01.json','reports/local_coverage/coverage_shard_00_of_01.log',
      'reports/local_coverage/.coverage.00_of_01',
    }


def test_source_archive_does_not_treat_local_coverage_as_source_report():
    assert srcpkg._report_allowed(Path('reports/local_coverage/full_coverage_manifest.json')) is False
    assert srcpkg._report_allowed(Path('reports/LATEST_COVERAGE.txt')) is True
