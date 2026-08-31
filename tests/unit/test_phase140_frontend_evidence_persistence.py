from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_frontend_browser_acceptance_persists_auditable_run_evidence():
    source = (ROOT / "scripts/external/frontend_browser_acceptance.py").read_text(encoding="utf-8")
    assert 'frontend_browser_runs' in source
    assert 'viewport_{w}x{h}.png' in source
    assert 'viewport_{w}x{h}.html' in source
    assert 'root_rendered' in source
    assert 'manifest_sha256' in source
    assert 'git_commit_sha' in source
    assert '--version' in source
    assert 'TemporaryDirectory' not in source


def test_readiness_dossier_runs_standalone_frontend_browser_after_locks_without_changing_canonical_profiles():
    dossier = (ROOT / "scripts/production_readiness_dossier.py").read_text(encoding="utf-8")
    assert '"name": "frontend_browser"' in dossier
    assert 'standalone_readiness_not_canonical_external_profile' in dossier
    assert 'scripts/external/frontend_browser_acceptance.py --confirm-real-target' in dossier
    orchestrator = (ROOT / "scripts/production_acceptance_orchestrator.py").read_text(encoding="utf-8")
    # The canonical external-evidence profile set remains intentionally unchanged.
    profiles_block = orchestrator.split('PROFILES = (', 1)[1].split(')', 1)[0]
    assert 'frontend-browser' not in profiles_block
