from backend.app.release.blocker_dossier import classify_requirement
from scripts.verify_external_execution_plan import build


def test_section99_umbrella_requirements_are_external_restart_drills():
    assert classify_requirement(99, "Bölüm 99 ADVANCED TESTING / FAULT INJECTION hükümleri") == (
        "RUNTIME_FAULT_DRILL",
        True,
    )
    assert classify_requirement(99, "kritik senaryolarını test et.") == (
        "RUNTIME_FAULT_DRILL",
        True,
    )


def test_all_open_requirements_have_non_ambiguous_consistent_external_plan():
    payload = build()
    assert payload["open_requirement_count"] == 100
    assert payload["mapped_requirement_count"] == 100
    assert payload["p0_open_requirement_count"] == 42
    assert payload["ambiguous_p0_requirement_ids"] == []
    assert payload["problems"] == []
    assert payload["verified"] is True


def test_section99_p0_umbrella_ids_map_to_restart_drills():
    payload = build()
    rows = {row["requirement_id"]: row for row in payload["mappings"]}
    for rid in ("REQ-V51-099-001", "REQ-V51-099-020"):
        assert rows[rid]["profile"] == "restart-drills"
        assert rows[rid]["blocker_category"] == "RUNTIME_FAULT_DRILL"
        assert rows[rid]["external_required"] is True
