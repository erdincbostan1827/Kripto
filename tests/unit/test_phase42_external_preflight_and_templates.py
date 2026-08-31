from pathlib import Path

from scripts.external.generate_drill_template import template
from scripts.external_acceptance_preflight import evaluate


def test_preflight_covers_all_external_profiles(monkeypatch) -> None:
    for name in (
        "BINANCE_TESTNET_API_KEY", "BINANCE_TESTNET_API_SECRET", "PITR_DRILL_COMMAND", "PITR_EVIDENCE_JSON",
        "HA_DRILL_COMMAND", "HA_EVIDENCE_JSON", "WORM_ACCEPTANCE_COMMAND", "WORM_EVIDENCE_JSON",
    ):
        monkeypatch.delenv(name, raising=False)
    payload = evaluate()
    assert payload["classification"] == "EXTERNAL_ACCEPTANCE_PREFLIGHT_ONLY_NOT_ACCEPTANCE_EVIDENCE"
    assert {"dependency_locks", "container_runtime", "credentialed_testnet", "transferred_supply_chain_contract", "pitr_contract", "ha_contract", "worm_contract", "signing_tooling"} <= set(payload["groups"])
    assert payload["all_external_prerequisites_ready"] is False


def test_templates_are_fail_closed_and_bound_to_current_git() -> None:
    for kind in ("pitr", "ha", "worm"):
        payload = template(kind)
        assert payload["real_system"] is False
        assert len(payload["git_commit_sha"]) == 40
        assert payload["artifacts"][0]["path"].startswith("REPLACE_")
        booleans = [v for k, v in payload.items() if k not in {"real_system"} and isinstance(v, bool)]
        assert booleans and not any(booleans)
