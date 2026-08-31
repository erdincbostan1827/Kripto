from pathlib import Path
import json
import yaml

from scripts import generate_project_status as status
from scripts.release_gate import REQUIRED_EXTERNAL_ACCEPTANCE


def test_project_status_uses_canonical_release_gate_external_keys(tmp_path: Path, monkeypatch) -> None:
    matrix = {"requirements": [{"requirement_id":"P0","priority":"P0","status":"PASS"}]}
    (tmp_path/"requirements_acceptance_matrix.yaml").write_text(yaml.safe_dump(matrix))
    acceptance = {key: "PASS" for key in REQUIRED_EXTERNAL_ACCEPTANCE}
    acceptance["worm_audit_storage"] = "NOT_TESTED"
    (tmp_path/"RELEASE_MANIFEST.json").write_text(json.dumps({"acceptance": acceptance}))
    (tmp_path/"reports").mkdir(); (tmp_path/"reports/TEST_COUNT.txt").write_text("1 tests collected\n")
    (tmp_path/"reports/LATEST_COVERAGE.txt").write_text("TOTAL 1 0 100%\n")
    (tmp_path/"uv.lock").write_text("x"); (tmp_path/"frontend").mkdir(); (tmp_path/"frontend/package-lock.json").write_text("{}")
    monkeypatch.setattr(status, "ROOT", tmp_path)
    monkeypatch.setattr(status, "MATRIX", tmp_path/"requirements_acceptance_matrix.yaml")
    monkeypatch.setattr(status, "MANIFEST", tmp_path/"RELEASE_MANIFEST.json")
    result = status.build()
    assert "worm_audit_storage=NOT_TESTED" in result["blockers"]
    assert all(any(b.startswith(key + "=") for b in result["blockers"]) == (acceptance[key] != "PASS") for key in REQUIRED_EXTERNAL_ACCEPTANCE)
