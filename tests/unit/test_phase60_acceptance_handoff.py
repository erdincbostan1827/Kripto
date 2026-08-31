from pathlib import Path
import subprocess

from scripts.production_acceptance_handoff import build_handoff, REQUIRED_SECRETS


def _git(root: Path, *args: str):
    subprocess.check_call(['git', *args], cwd=root, stdout=subprocess.DEVNULL)


def test_phase60_handoff_is_candidate_bound_but_never_acceptance_evidence(tmp_path: Path):
    _git(tmp_path, 'init')
    _git(tmp_path, 'config', 'user.email', 'test@example.com')
    _git(tmp_path, 'config', 'user.name', 'Test')
    (tmp_path/'x').write_text('x')
    _git(tmp_path, 'add', 'x')
    _git(tmp_path, 'commit', '-m', 'x')
    sha = subprocess.check_output(['git','rev-parse','HEAD'], cwd=tmp_path, text=True).strip()
    payload = build_handoff(tmp_path)
    assert payload['candidate_git_sha'] == sha
    assert payload['classification'] == 'ACCEPTANCE_HANDOFF_NOT_ACCEPTANCE_EVIDENCE'
    assert payload['release_status']['prod_live_status'] == 'BLOCKED'
    assert payload['release_status']['default_mode'] == 'PAPER'
    assert payload['release_status']['live_enabled'] is False


def test_phase60_handoff_lists_protected_runner_and_all_external_secret_contracts(tmp_path: Path):
    _git(tmp_path, 'init')
    _git(tmp_path, 'config', 'user.email', 'test@example.com')
    _git(tmp_path, 'config', 'user.name', 'Test')
    (tmp_path/'x').write_text('x')
    _git(tmp_path, 'add', 'x')
    _git(tmp_path, 'commit', '-m', 'x')
    payload = build_handoff(tmp_path)
    assert payload['required_runner_labels'] == ['self-hosted','production-acceptance']
    assert payload['protected_environment'] == 'production-acceptance'
    assert payload['required_secrets'] == REQUIRED_SECRETS
    assert payload['source_file_presence'] == {'uv.lock': False, 'frontend/package-lock.json': False}


def test_phase60_handoff_is_in_source_and_evidence_canonical_package_policies():
    from scripts import package_release, package_evidence
    assert 'PRODUCTION_ACCEPTANCE_HANDOFF.json' in package_release.CANONICAL_REPORT_FILES
    assert 'reports/PRODUCTION_ACCEPTANCE_HANDOFF.json' in package_evidence.CANONICAL_FILES


def test_phase60_orchestrator_plan_surfaces_handoff_without_external_execution(monkeypatch, tmp_path):
    import scripts.production_acceptance_orchestrator as orch
    monkeypatch.setattr(orch, 'ROOT', tmp_path)
    monkeypatch.setattr(orch, 'build_handoff', lambda root: {'classification': 'ACCEPTANCE_HANDOFF_NOT_ACCEPTANCE_EVIDENCE'})
    result = orch.orchestrate(confirm_real=False)
    assert result['executed'] is False
    assert result['handoff']['classification'] == 'ACCEPTANCE_HANDOFF_NOT_ACCEPTANCE_EVIDENCE'
