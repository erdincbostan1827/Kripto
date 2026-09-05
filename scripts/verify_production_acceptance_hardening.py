from __future__ import annotations

from pathlib import Path

WORKFLOW = Path('.github/workflows/production-acceptance.yml')
EVIDENCE_WORKFLOW = Path('.github/workflows/phase225-production-build-evidence.yml')
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
PREFLIGHT_COMMAND = 'python scripts/production_acceptance_preflight.py'
ORCHESTRATOR_COMMAND = 'python scripts/production_acceptance_orchestrator.py --confirm-real-target'
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
    PREFLIGHT_COMMAND,
    'reports/production_acceptance/PRODUCTION_ACCEPTANCE_PREFLIGHT.json',
    'reports/production_acceptance/**',
    'EXPECTED_ACCEPTANCE_SHA: ${{ needs.ci-build-evidence.outputs.source_sha }}',
    'EXPECTED_CONTAINER_DIGEST: ${{ needs.ci-build-evidence.outputs.container_digest }}',
    ORCHESTRATOR_COMMAND,
    'actions/download-artifact@d3f86a106a0bac45b974a628896c90dbdf5c8093',
)
EVIDENCE_TRIGGER_SNIPPETS = (
    "- 'backend/**'",
    "- 'scripts/**'",
    "- 'config/**'",
    "- 'tests/**'",
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
    if PREFLIGHT_COMMAND in text and ORCHESTRATOR_COMMAND in text:
        preflight_index = text.index(PREFLIGHT_COMMAND)
        orchestrator_index = text.index(ORCHESTRATOR_COMMAND)
        if preflight_index >= orchestrator_index:
            problems.append('REAL_TARGET_PREFLIGHT_NOT_BEFORE_ORCHESTRATOR')
        elif 'continue-on-error' in text[preflight_index:orchestrator_index]:
            problems.append('REAL_TARGET_PREFLIGHT_CONTINUE_ON_ERROR_FORBIDDEN')
    return problems


def _trigger_block(text: str, trigger: str, next_trigger: str | None = None) -> str:
    marker = f'\n  {trigger}:\n'
    if marker not in text:
        return ''
    block = text.split(marker, 1)[1]
    if next_trigger is not None:
        next_marker = f'\n  {next_trigger}:\n'
        if next_marker in block:
            block = block.split(next_marker, 1)[0]
    return block


def verify_evidence_trigger_text(text: str) -> list[str]:
    problems: list[str] = []
    push_block = _trigger_block(text, 'push', 'pull_request')
    pull_request_block = _trigger_block(text, 'pull_request')

    if not push_block:
        problems.append('EVIDENCE_PUSH_TRIGGER_MISSING')
    elif 'paths:' in push_block:
        problems.append('EVIDENCE_MAIN_PUSH_MUST_NOT_BE_PATH_FILTERED')

    if not pull_request_block:
        problems.append('EVIDENCE_PULL_REQUEST_TRIGGER_MISSING')
    else:
        for snippet in EVIDENCE_TRIGGER_SNIPPETS:
            if snippet not in pull_request_block:
                problems.append(f'EVIDENCE_PR_TRIGGER_COVERAGE_MISSING:{snippet}')
    return problems


def main() -> int:
    text = WORKFLOW.read_text(encoding='utf-8')
    evidence_text = EVIDENCE_WORKFLOW.read_text(encoding='utf-8')
    problems = verify_text(text)
    problems.extend(verify_evidence_trigger_text(evidence_text))
    if problems:
        print('\n'.join(problems))
        return 2
    print('PRODUCTION_ACCEPTANCE_HARDENING=PASS')
    print('uv_version=0.12.9')
    print('scanner_toolchain=pip-audit==2.10.1,bandit==1.9.4,semgrep==1.175.0,cyclonedx-bom==7.3.1,pip-licenses==5.5.5')
    print('bandit_policy=reviewed-finding-set-fingerprint+new-or-changed-findings-fail')
    print('runtime_image_build=backend/Dockerfile:runtime')
    print('ghcr_identity=lowercase_repository+exact_git_sha')
    print('evidence_trigger_coverage=unfiltered-main-push+backend+scripts+config+tests:on-pull-request')
    print('real_target_preflight=required+fail-closed+redacted-evidence')
    print('real_target_boundary=self-hosted+production-acceptance+challenge-trust')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
