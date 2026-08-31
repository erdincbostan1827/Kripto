from pathlib import Path
from scripts.external.generate_dependency_license_report import build
from scripts.external_acceptance_runner import build_plan

def test_dependency_license_report_is_fail_closed_without_locks():
    r=build()
    assert r['verified'] is False
    assert 'UV_LOCK_MISSING' in r['problems']
    assert 'FRONTEND_LOCK_MISSING' in r['problems']
    assert not Path('reports/external_acceptance/dependency_licenses.json').exists()

def test_license_preflight_is_not_mixed_with_transferred_ci_supply_chain_acceptance():
    keys=[x[0] for x in build_plan('supply-chain')]
    assert keys == ['transferred_supply_chain_verification']
