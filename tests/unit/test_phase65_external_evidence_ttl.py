from __future__ import annotations

import json
import subprocess
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from pathlib import Path

from backend.app.release.acceptance_challenge import create_challenge
from backend.app.release.evidence_ledger import append_entry
from backend.app.release.acceptance_contract import command_contract, command_contract_sha256
from scripts.verify_external_acceptance import DEFAULT_GROUP_TTL_HOURS, verify_manifest


def _git(root: Path) -> str:
    subprocess.run(["git","init","-q"], cwd=root, check=True)
    subprocess.run(["git","config","user.email","p65@example.invalid"], cwd=root, check=True)
    subprocess.run(["git","config","user.name","P65"], cwd=root, check=True)
    (root/"seed").write_text("x")
    subprocess.run(["git","add","seed"], cwd=root, check=True)
    subprocess.run(["git","commit","-qm","seed"], cwd=root, check=True)
    return subprocess.check_output(["git","rev-parse","HEAD"], cwd=root, text=True).strip()


def _runtime_manifest(root: Path, observed_at: str) -> Path:
    sha = _git(root)
    reports = root/"reports/external_acceptance"
    reports.mkdir(parents=True)
    challenge = create_challenge(root, reports/"release_challenge.json")
    run_id="phase65-runtime-run"
    run_dir=reports/"runs"/run_id/"runtime"; run_dir.mkdir(parents=True, exist_ok=True)
    rows=[]
    contract = command_contract("runtime")
    for key in ("docker_compose_config","docker_compose_up","postgres_migration","redis_ping","runtime_health"):
        log=run_dir/f"{key}.log"; log.write_text("ok")
        rows.append({"key":key,"status":"PASS","real_system":True,"command":contract[key],"exit_code":0,"blocker":None,"artifact":str(log.relative_to(root)),"sha256":sha256(log.read_bytes()).hexdigest(),"observed_at":observed_at})
    payload={"schema_version":"3.2","run_id":run_id,"generated_at":datetime.now(timezone.utc).isoformat(),"classification":"EXTERNAL_ACCEPTANCE_EVIDENCE_BUNDLE","profile":"runtime","command_contract_sha256":command_contract_sha256("runtime"),"real_target_explicitly_confirmed":True,"challenge":challenge,"environment":{"git_commit_sha":sha,"acceptance_environment_id_hash":"a"*64,"topology_hash":"b"*64},"evidence":rows,"groups":{"runtime":"PASS"},"selected_all_pass":True}
    path=reports/"manifest_runtime.json"; path.write_text(json.dumps(payload))
    append_entry(reports/"evidence_ledger.json", manifest_sha256=sha256(path.read_bytes()).hexdigest(), challenge_id=challenge["challenge_id"], git_commit_sha=sha, profile="runtime", root=root)
    return path


def test_phase65_runtime_rows_expire_independently_of_fresh_manifest(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("ACCEPTANCE_CHALLENGE_VERIFY_COMMAND", "true")
    path=_runtime_manifest(tmp_path, (datetime.now(timezone.utc)-timedelta(hours=25)).isoformat())
    result=verify_manifest(path, root=tmp_path)
    assert result["verified"] is False
    assert result["groups"]["runtime"] == "BLOCKED"
    assert any("EVIDENCE_ROW_STALE_OR_INVALID_TIME:runtime" in p for p in result["problems"])


def test_phase65_ttl_override_is_explicit_and_reported(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("ACCEPTANCE_CHALLENGE_VERIFY_COMMAND", "true")
    path=_runtime_manifest(tmp_path, (datetime.now(timezone.utc)-timedelta(hours=25)).isoformat())
    result=verify_manifest(path, root=tmp_path, group_ttl_hours={"runtime":48})
    assert result["verified"] is True
    assert result["groups"]["runtime"] == "PASS"
    assert result["effective_group_ttl_hours"]["runtime"] == 48


def test_phase65_default_ttl_policy_is_conservative_for_operational_groups():
    for group in ("runtime","restart_drills","pitr","ha","worm","testnet","private_stream","live_shadow"):
        assert DEFAULT_GROUP_TTL_HOURS[group] == 24
