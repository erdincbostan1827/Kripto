from __future__ import annotations

import scripts.production_readiness_dossier as dossier


def test_dossier_is_plan_only_and_covers_every_current_p0_blocker() -> None:
    payload = dossier.build()
    assert payload["classification"] == "PRODUCTION_READINESS_DOSSIER_NOT_ACCEPTANCE_EVIDENCE"
    assert "cannot promote" in payload["truth_policy"].lower()
    counted = sum(v["count"] for v in payload["blockers_by_category"].values())
    assert counted == payload["p0_blocker_count"]
    assert payload["p0_blocker_count"] > 0


def test_dossier_workflow_requires_challenge_before_real_profiles() -> None:
    payload = dossier.build()
    workflow = payload["workflow"]
    assert workflow[0]["name"] == "create_release_challenge"
    assert "generate_acceptance_challenge.py" in workflow[0]["command"]
    assert all("--confirm-real-target" in row["command"] for row in workflow[1:10])


def test_dossier_preserves_manual_market_evidence_blockers() -> None:
    payload = dossier.build()
    joined = " ".join(payload["manual_external_evidence_still_required"]).lower()
    assert "private" in joined and "paper" in joined and "shadow" in joined and "profitability" in joined
