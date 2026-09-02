from pathlib import Path

import yaml

from scripts.external.execution_map import build
from scripts.external.tauri_build_readiness import evaluate

ROOT = Path(__file__).resolve().parents[2]


def test_phase143_all_open_requirements_have_non_ambiguous_external_execution_profile():
    payload = build()
    assert payload['classification'] == 'EXTERNAL_ACCEPTANCE_EXECUTION_MAP_NOT_ACCEPTANCE_EVIDENCE'
    matrix = yaml.safe_load((ROOT / 'requirements_acceptance_matrix.yaml').read_text(encoding='utf-8'))
    open_count = sum(row['status'] == 'NOT_TESTED' for row in matrix['requirements'])
    assert payload['open_requirement_count'] == open_count
    assert payload['mapped_requirement_count'] == open_count
    assert payload['unmapped_requirement_count'] == 0
    assert len(payload['requirements']) == open_count
    assert all(row['profile'] not in {'manual_review','LOCAL_OR_AMBIGUOUS'} for row in payload['requirements'])
    ids = {row['requirement_id']: row for row in payload['requirements']}
    assert ids['REQ-V51-099-001']['profile'] == 'restart-drills'
    assert ids['REQ-V51-099-020']['profile'] == 'restart-drills'
    assert ids['REQ-V51-168-026']['profile'] == 'frontend-browser'
    assert ids['REQ-V51-169-010']['profile'] == 'desktop-build'
    assert 'cannot promote' in payload['truth_policy']


def test_phase143_tauri_build_readiness_recognizes_frontend_lock_and_fails_closed_without_rust():
    result = evaluate(confirm_real=False, timeout=1)
    assert result['classification'] == 'REAL_TAURI_BUILD_READINESS_NOT_SIGNING_EVIDENCE'
    assert result['verified'] is False
    assert 'REAL_TARGET_NOT_EXPLICITLY_CONFIRMED' in result['blockers']
    assert 'FRONTEND_LOCK_MISSING' not in result['blockers']
    assert 'TAURI_CARGO_LOCK_MISSING' in result['blockers']
    assert 'signing' in result['truth_policy'].lower()


def test_phase143_tauri_manifest_uses_exact_dependencies_but_lock_is_not_fabricated():
    cargo = (ROOT/'frontend/src-tauri/Cargo.toml').read_text(encoding='utf-8')
    assert 'tauri = "=2.11.5"' in cargo
    assert 'tauri-build = "=2.6.3"' in cargo
    assert not (ROOT/'frontend/src-tauri/Cargo.lock').exists()


def test_phase143_readiness_dossier_includes_execution_map_and_desktop_build_without_promoting_profiles():
    source = (ROOT/'scripts/production_readiness_dossier.py').read_text(encoding='utf-8')
    assert 'map_all_open_requirements' in source
    assert 'scripts/external/execution_map.py' in source
    assert 'inventory_external_toolchain' in source
    assert 'desktop_build' in source
    assert 'scripts/external/tauri_build_readiness.py --confirm-real-target' in source
    assert 'standalone_readiness_not_signing_evidence' in source
