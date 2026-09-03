from pathlib import Path

from scripts.verify_production_acceptance_hardening import (
    EXPECTED_BANDIT_REPORT,
    EXPECTED_BANDIT_VERIFY,
    EXPECTED_RUNTIME_BUILD,
    EXPECTED_SCANNERS,
    EXPECTED_UV,
    verify_text,
)


def _valid_workflow_text() -> str:
    return "\n".join(
        [
            EXPECTED_UV,
            EXPECTED_SCANNERS,
            'REPOSITORY_LC="${GITHUB_REPOSITORY,,}"',
            'IMAGE="ghcr.io/${REPOSITORY_LC}/acceptance:${SHA}"',
            EXPECTED_RUNTIME_BUILD,
            'uv export --locked --no-dev --no-emit-project --format requirements-txt',
            EXPECTED_BANDIT_REPORT,
            EXPECTED_BANDIT_VERIFY,
            'runs-on: [self-hosted, production-acceptance]',
            'environment: production-acceptance',
            'ACCEPTANCE_REQUIRE_CHALLENGE_TRUST: "1"',
            'python scripts/production_acceptance_orchestrator.py --confirm-real-target',
            'actions/download-artifact@d3f86a106a0bac45b974a628896c90dbdf5c8093',
        ]
    )


def test_valid_workflow_passes() -> None:
    assert verify_text(_valid_workflow_text()) == []


def test_unpinned_scanner_toolchain_is_rejected() -> None:
    text = _valid_workflow_text().replace(
        EXPECTED_SCANNERS,
        'python -m pip install pip-audit bandit semgrep cyclonedx-bom pip-licenses',
    )
    problems = verify_text(text)
    assert 'SCANNER_TOOLCHAIN_NOT_EXACTLY_PINNED' in problems
    assert any(item.startswith('FORBIDDEN_REGRESSION:python -m pip install pip-audit') for item in problems)


def test_mixed_case_repository_expression_is_rejected() -> None:
    text = _valid_workflow_text().replace(
        'REPOSITORY_LC="${GITHUB_REPOSITORY,,}"\nIMAGE="ghcr.io/${REPOSITORY_LC}/acceptance:${SHA}"',
        'IMAGE="ghcr.io/${{ github.repository }}/acceptance:${SHA}"',
    )
    problems = verify_text(text)
    assert any(item.startswith('MISSING_REQUIRED_INVARIANT:REPOSITORY_LC=') for item in problems)
    assert any(item.startswith('FORBIDDEN_REGRESSION:IMAGE=') for item in problems)


def test_root_dockerfile_build_regression_is_rejected() -> None:
    text = _valid_workflow_text().replace(
        EXPECTED_RUNTIME_BUILD,
        'docker build -t "$ACCEPTANCE_CONTAINER_IMAGE" .',
    )
    problems = verify_text(text)
    assert any(item.startswith('MISSING_REQUIRED_INVARIANT:docker build --file backend/Dockerfile') for item in problems)
    assert any(item.startswith('FORBIDDEN_REGRESSION:docker build -t') for item in problems)


def test_bandit_fingerprint_gate_cannot_be_removed() -> None:
    text = _valid_workflow_text().replace(EXPECTED_BANDIT_REPORT, 'bandit -q -r backend scripts')
    text = text.replace(EXPECTED_BANDIT_VERIFY, '')
    problems = verify_text(text)
    assert f'MISSING_REQUIRED_INVARIANT:{EXPECTED_BANDIT_REPORT}' in problems
    assert f'MISSING_REQUIRED_INVARIANT:{EXPECTED_BANDIT_VERIFY}' in problems


def test_real_target_trust_boundary_cannot_be_removed() -> None:
    text = _valid_workflow_text().replace('ACCEPTANCE_REQUIRE_CHALLENGE_TRUST: "1"', '')
    problems = verify_text(text)
    assert 'MISSING_REQUIRED_INVARIANT:ACCEPTANCE_REQUIRE_CHALLENGE_TRUST: "1"' in problems


def test_watchdog_does_not_regress_to_dynamic_urllib() -> None:
    source = Path('scripts/watchdog_runner.py').read_text(encoding='utf-8')
    assert 'urllib.request' not in source
    assert 'import httpx' in source
    assert 'follow_redirects=False' in source
    assert 'validate_http_url(' in source
