from pathlib import Path
import json

from scripts.test_inventory import parse_test_count_text, parse_collection, read_verified

ROOT = Path(__file__).resolve().parents[2]


def test_phase146_test_count_parser_accepts_canonical_and_legacy_formats():
    assert parse_test_count_text('950 tests collected\n') == 950
    assert parse_test_count_text('950\n') == 950
    assert parse_test_count_text('tests/a.py: 2\ntests/b.py: 3\n') == 5
    assert parse_collection('tests/a.py: 2\ntests/b.py: 3\n') == (5, 2)


def test_phase146_release_truth_uses_git_bound_test_inventory_source():
    release = (ROOT / 'scripts/generate_release_manifest.py').read_text(encoding='utf-8')
    status = (ROOT / 'scripts/generate_project_status.py').read_text(encoding='utf-8')
    consistency = (ROOT / 'scripts/verify_release_consistency.py').read_text(encoding='utf-8')
    assert 'read_test_inventory' in release
    assert 'read_test_inventory' in status
    assert 'read_test_inventory' in consistency


def test_phase146_test_inventory_is_packaged_as_canonical_evidence():
    evidence = (ROOT / 'scripts/package_evidence.py').read_text(encoding='utf-8')
    release = (ROOT / 'scripts/package_release.py').read_text(encoding='utf-8')
    assert 'reports/TEST_INVENTORY.json' in evidence
    assert 'reports/TEST_COLLECTION.txt' in evidence
    assert 'TEST_INVENTORY.json' in release
    assert 'TEST_COLLECTION.txt' in release
