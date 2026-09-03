from __future__ import annotations

from pathlib import Path

WORKFLOW = Path('.github/workflows/production-acceptance.yml')
EXPECTED_UV = "UV_VERSION: '0.12.9'"
EXPECTED_SCANNERS = (
    "python -m pip install "
    "'pip-audit==2.10.1' "
    "'bandit==1.9.4' "
    "'semgrep==1.175.0' "
    "'cyclonedx-bom==7.3.1' "
    "'pip-licenses==5.5.5'"
)
EXPECTED_RUNTIME_BUILD = (
    'docker build --file backend/Dockerfile --target runtime '
    '-t "$ACCEPTANCE_CONTAINER_IMAGE" .'
)
EXPECTED_BANDIT_REPORT = (
    'bandit -q -r backend scripts -f json '
    '-o reports/external_acceptance/bandit-report.json'
)
EXPECTED_BANDIT_VERIFY = (
    'python scripts/external/verify_bandit_baseline.py '
    'reports/external_acceptance/bandit-report.json'
)
REQUIRED_SNIPPETS = (
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
)
FORBIDDEN_SNIPPETS = (
    "UV_VERSION: '0.10.0'",
    'IMAGE="ghcr.io/${{ github.repository }}/acceptance:${SHA}"',
    'docker build -t "$ACCEPTANCE_CONTAINER_IMAGE" .',
    'python -m pip install pip-audit bandit semgrep cyclonedx-bom pip-licenses',
)


def verify_text(text: str) -> list[str]:
    problems: list[str] = []
    if EXPECTED_UV not in text:
        problems.append('UV_VERSION_NOT_PINNED_TO_CI_PARITY')
    if EXPECTED_SCANNERS not in text:
        problems.append('SCANNER_TOOLCHAIN_NOT_EXACTLY_PINNED')
    for snippet in REQUIRED_SNIPPETS:
        if snippet not in text:
            problems.append(f'MISSING_REQUIRED_INVARIANT:{snippet}')
    for snippet in FORBIDDEN_SNIPPETS:
        if snippet in text:
            problems.append(f'FORBIDDEN_REGRESSION:{snippet}')
    return problems


def main() -> int:
    text = WORKFLOW.read_text(encoding='utf-8')
    problems = verify_text(text)
    if problems:
        print('\n'.join(problems))
        return 2
    print('PRODUCTION_ACCEPTANCE_HARDENING=PASS')
    print('uv_version=0.12.9')
    print('scanner_toolchain=pip-audit==2.10.1,bandit==1.9.4,semgrep==1.175.0,cyclonedx-bom==7.3.1,pip-licenses==5.5.5')
    print('bandit_policy=reviewed-finding-set-fingerprint+new-or-changed-findings-fail')
    print('runtime_image_build=backend/Dockerfile:runtime')
    print('ghcr_identity=lowercase_repository+exact_git_sha')
    print('real_target_boundary=self-hosted+production-acceptance+challenge-trust')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
