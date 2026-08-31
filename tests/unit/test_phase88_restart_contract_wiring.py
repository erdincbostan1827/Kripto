from __future__ import annotations

from pathlib import Path

import scripts.external_acceptance_preflight as preflight


def test_preflight_includes_restart_contract(monkeypatch):
    for name in ('RESTART_DRILL_COMMAND', 'RESTART_EVIDENCE_JSON'):
        monkeypatch.delenv(name, raising=False)
    result = preflight.evaluate()
    assert result['groups']['restart_contract'] is False
    keys = {row['key'] for row in result['checks']}
    assert 'env:RESTART_DRILL_COMMAND' in keys
    assert 'env:RESTART_EVIDENCE_JSON' in keys


def test_production_workflow_passes_restart_contract_to_orchestrator():
    root = Path(__file__).resolve().parents[2]
    text = (root / '.github/workflows/production-acceptance.yml').read_text()
    marker = text.split('- name: Run fail-closed real-target orchestrator', 1)[1]
    assert 'RESTART_DRILL_COMMAND: ${{ secrets.RESTART_DRILL_COMMAND }}' in marker
    assert 'RESTART_EVIDENCE_JSON: ${{ secrets.RESTART_EVIDENCE_JSON }}' in marker
