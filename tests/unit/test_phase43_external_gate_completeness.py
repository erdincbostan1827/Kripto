from scripts.external_acceptance_runner import build_plan
from scripts.generate_release_manifest import acceptance_statuses
from scripts.release_gate import REQUIRED_EXTERNAL_ACCEPTANCE
from scripts.verify_external_acceptance import GROUP_KEYS


def test_external_group_contracts_cover_restart_ha_and_worm() -> None:
    assert "restart_drills" in GROUP_KEYS
    assert "ha" in GROUP_KEYS
    assert "worm" in GROUP_KEYS
    assert len(build_plan("restart-drills")) == 5
    assert build_plan("worm")[0][0] == "worm_storage"


def test_release_manifest_and_gate_include_all_new_p0_external_controls() -> None:
    statuses = acceptance_statuses({"groups": {}})
    required = {
        "redis_restart_drill", "postgres_restart_drill", "pitr_restore_drill", "ha_failover_drill", "worm_audit_storage"
    }
    assert required <= statuses.keys()
    assert required <= set(REQUIRED_EXTERNAL_ACCEPTANCE)
    assert all(statuses[key] == "NOT_TESTED" for key in required)


def test_verified_groups_promote_only_matching_acceptance_fields() -> None:
    statuses = acceptance_statuses({"groups": {"restart_drills": "PASS", "ha": "PASS", "worm": "PASS"}})
    assert statuses["redis_restart_drill"] == "PASS"
    assert statuses["postgres_restart_drill"] == "PASS"
    assert statuses["ha_failover_drill"] == "PASS"
    assert statuses["worm_audit_storage"] == "PASS"
    assert statuses["pitr_restore_drill"] == "NOT_TESTED"
