from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / '.github' / 'workflows' / 'production-acceptance.yml'


def _workflow():
    return yaml.safe_load(WORKFLOW.read_text(encoding='utf-8'))


def test_phase59_workflow_is_manual_and_fail_closed():
    data = _workflow()
    trigger = data.get('on') or data.get(True)
    assert 'workflow_dispatch' in trigger
    assert set(data['jobs']) == {'ci-build-evidence', 'real-target-acceptance'}
    assert data['jobs']['real-target-acceptance']['environment'] == 'production-acceptance'
    assert data['jobs']['real-target-acceptance']['runs-on'] == ['self-hosted', 'production-acceptance']


def test_phase59_ci_build_evidence_has_lock_test_scan_sbom_and_provenance_chain():
    text = WORKFLOW.read_text(encoding='utf-8')
    required = [
        'verify_source_locks.py', 'uv lock --locked', 'npm ci',
        'local_acceptance_runner.py', 'merge_local_acceptance.py', 'verify_local_acceptance.py',
        'pip-audit', 'bandit', 'semgrep', 'gitleaks', 'trivy', 'syft', 'pip-licenses', 'sbom.cdx.json',
        'dependency_licenses.json', 'verify_supply_chain_artifacts.py',
        'provenance_capture.py', 'CI_RUN_ID', 'CI_COMMIT_SHA', 'docker push', 'docker pull',
    ]
    for token in required:
        assert token in text


def test_phase59_real_target_job_uses_existing_fail_closed_orchestrator_and_secrets():
    text = WORKFLOW.read_text(encoding='utf-8')
    assert 'production_acceptance_orchestrator.py --confirm-real-target' in text
    for token in [
        'BINANCE_TESTNET_API_KEY', 'BINANCE_TESTNET_API_SECRET',
        'PITR_DRILL_COMMAND', 'HA_DRILL_COMMAND', 'WORM_ACCEPTANCE_COMMAND',
        'PROVENANCE_SIGN_VERIFY_COMMAND',
    ]:
        assert token in text
    assert 'release_gate.py' in text


def test_phase59_workflow_never_enables_live_mode():
    text = WORKFLOW.read_text(encoding='utf-8').lower()
    assert 'live_enabled=true' not in text
    assert 'mode=live' not in text
    assert 'prod_live_release=pass' not in text


def test_phase59_manual_ref_sha_binds_image_and_downloaded_evidence_across_jobs():
    text = WORKFLOW.read_text(encoding='utf-8')
    assert 'acceptance:${SHA}' in text
    assert 'container_image: ${{ steps.identity.outputs.container_image }}' in text
    assert 'actions/download-artifact@d3f86a106a0bac45b974a628896c90dbdf5c8093' in text
    assert 'ci-build-evidence-${{ needs.ci-build-evidence.outputs.source_sha }}' in text
    assert 'ACCEPTANCE_CONTAINER_IMAGE: ${{ needs.ci-build-evidence.outputs.container_image }}' in text
    assert "CI_COMMIT_SHA: ${{ needs.ci-build-evidence.outputs.source_sha }}" in text
    assert 'acceptance:${{ github.sha }}' not in text


def test_phase59_supply_chain_images_are_not_floating_latest_and_target_has_required_clis():
    text = WORKFLOW.read_text(encoding='utf-8')
    assert ':latest' not in text
    assert 'ghcr.io/gitleaks/gitleaks:v8.28.0' in text
    assert 'aquasec/trivy:0.65.0' in text
    assert 'anchore/syft:v1.32.0' in text
    assert 'Provision exact acceptance Python CLI toolchain from CI receipt' in text
    assert 'ci_toolchain_receipt.py pip-specs' in text
    assert 'CI_TOOLCHAIN_RECEIPT.json' in text
    assert 'reports/CI_SCANNER_VERSIONS.txt' in text


def test_phase59_permissions_are_least_privilege_and_secrets_stay_on_real_target_job():
    data = _workflow()
    assert data['permissions'] == {'contents': 'read'}
    build = data['jobs']['ci-build-evidence']
    target = data['jobs']['real-target-acceptance']
    assert build['permissions'] == {'contents': 'read', 'packages': 'write'}
    assert target['permissions'] == {'contents': 'read', 'id-token': 'write'}
    build_text = str(build)
    assert 'BINANCE_TESTNET_API_KEY' not in build_text
    assert 'PITR_DRILL_COMMAND' not in build_text
    assert 'WORM_ACCEPTANCE_COMMAND' not in build_text
