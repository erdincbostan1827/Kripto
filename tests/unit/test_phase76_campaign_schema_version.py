from __future__ import annotations

import json
from pathlib import Path

from scripts.external.generate_campaign_evidence_templates import templates


def test_generated_campaign_templates_are_schema_versioned():
    docs = templates()
    assert docs
    assert all(doc.get("schema_version") == "1.0" for doc in docs.values())


def test_campaign_unknown_or_missing_schema_fails_closed(tmp_path: Path):
    from tests.unit.test_phase52_campaign_acceptance_contracts import _base
    from backend.app.release.campaign_acceptance import verify_campaign_evidence

    metrics = {
        "effective_sample_size": 120, "calendar_days": 31, "market_regimes": ["trend", "range"],
        "long_examples": 30, "exit_examples": 30, "short_examples": 0, "active_market_type": "SPOT",
        "cost_stress_passed": True, "latency_stress_passed": True, "independent_oos_passed": True,
        "execution_divergence_bps": 12.5, "real_market_data": True,
    }
    path = _base(tmp_path, "paper", metrics)
    doc = json.loads(path.read_text())
    doc.pop("schema_version", None)
    path.write_text(json.dumps(doc))
    result = verify_campaign_evidence(path, kind="paper", root=tmp_path)
    assert not result["verified"]
    assert "CAMPAIGN_SCHEMA_UNSUPPORTED" in result["problems"]

    doc["schema_version"] = "99.0"
    path.write_text(json.dumps(doc))
    result = verify_campaign_evidence(path, kind="paper", root=tmp_path)
    assert "CAMPAIGN_SCHEMA_UNSUPPORTED" in result["problems"]
