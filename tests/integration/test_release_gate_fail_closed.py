from __future__ import annotations

import json
import subprocess
from pathlib import Path

import yaml

from scripts.release_gate import REQUIRED_EXTERNAL_ACCEPTANCE, evaluate_release_gate


def _write_minimum_project(root: Path, external_status: str = "PASS") -> None:
    requirements = {
        "requirements": [
            {"requirement_id": "REQ-P0", "priority": "P0", "status": "PASS"},
        ]
    }
    root.joinpath("requirements_acceptance_matrix.yaml").write_text(
        yaml.safe_dump(requirements), encoding="utf-8"
    )
    root.joinpath("uv.lock").write_text("locked\n", encoding="utf-8")
    root.joinpath("frontend").mkdir()
    root.joinpath("frontend/package-lock.json").write_text("{}\n", encoding="utf-8")
    root.joinpath("reports").mkdir()
    for name in [
        "LATEST_PYTEST.txt",
        "LATEST_COVERAGE.txt",
        "ALEMBIC_OFFLINE_SQL.txt",
        "SECRET_SCAN.txt",
        "PROHIBITED_SCAN.txt",
        "DEPENDENCY_POLICY.txt",
    ]:
        root.joinpath("reports", name).write_text("PASS\n", encoding="utf-8")
    acceptance_keys = list(REQUIRED_EXTERNAL_ACCEPTANCE)
    manifest = {
        "prod_live_status": "ELIGIBLE_FOR_HUMAN_APPROVAL",
        "live_enabled": False,
        "default_mode": "PAPER",
        "test_evidence": {"status": "PASS", "verified": True},
        "acceptance": {key: external_status for key in acceptance_keys},
    }
    root.joinpath("RELEASE_MANIFEST.json").write_text(json.dumps(manifest), encoding="utf-8")
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=root, check=True)
    subprocess.run(["git", "add", "uv.lock", "frontend/package-lock.json"], cwd=root, check=True)
    subprocess.run(["git", "commit", "-qm", "locks"], cwd=root, check=True)


def test_release_gate_requires_external_acceptance_to_be_explicitly_pass(tmp_path: Path):
    _write_minimum_project(tmp_path, external_status="NOT_TESTED")
    blockers = evaluate_release_gate(tmp_path)
    assert any("credentialed_binance_testnet=NOT_TESTED" in blocker for blocker in blockers)
    assert any("pitr_restore_drill=NOT_TESTED" in blocker for blocker in blockers)


def test_release_gate_can_reach_human_approval_only_when_all_evidence_is_pass(tmp_path: Path):
    _write_minimum_project(tmp_path, external_status="PASS")
    assert evaluate_release_gate(tmp_path) == []
