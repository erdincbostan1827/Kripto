from scripts.external.toolchain_readiness import evaluate


def test_standalone_toolchain_readiness_reports_frontend_desktop_scanner_and_signing_without_canonical_promotion():
    result = evaluate()
    assert result['classification'] == 'STANDALONE_TOOLCHAIN_READINESS_NOT_ACCEPTANCE_EVIDENCE'
    assert 'frontend_browser_tooling' in result['groups']
    assert 'desktop_build_tooling' in result['groups']
    assert 'supply_chain_scanner_tooling' in result['groups']
    assert 'artifact_signing_tooling' in result['groups']
    names = {row['name'] for row in result['tools']}
    for name in ('chromium','cargo','rustc','pip-audit','bandit','semgrep','trivy','gitleaks','syft','pip-licenses','cosign'):
        assert name in names
    assert 'cannot promote' in result['truth_policy']
