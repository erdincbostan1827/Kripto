from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from backend.app.release.acceptance_challenge import create_challenge
from backend.app.release.acceptance_contract import command_contract, command_contract_sha256
from backend.app.release.evidence_ledger import append_entry
from scripts.verify_external_acceptance import verify_manifest


def _git(root: Path) -> str:
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.email", "p164@example.invalid"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.name", "P164"], cwd=root, check=True)
    (root / "seed").write_text("x", encoding="utf-8")
    subprocess.run(["git", "add", "seed"], cwd=root, check=True)
    subprocess.run(["git", "commit", "-qm", "seed"], cwd=root, check=True)
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()


def _runtime(root: Path, *, inside_run_dir: bool, include_run_id: bool = True) -> Path:
    sha = _git(root)
    reports = root / "reports" / "external_acceptance"
    reports.mkdir(parents=True, exist_ok=True)
    challenge = create_challenge(root, reports / "release_challenge.json")
    run_id = "phase164-runtime-run"
    run_dir = reports / "runs" / run_id / "runtime"
    run_dir.mkdir(parents=True, exist_ok=True)
    contract = command_contract("runtime")
    rows = []
    now = datetime.now(timezone.utc).isoformat()
    for key in ("docker_compose_config", "docker_compose_up", "postgres_migration", "redis_ping", "runtime_health"):
        log = (run_dir if inside_run_dir else reports) / f"{key}.log"
        log.write_text("ok\n", encoding="utf-8")
        rows.append({
            "key": key, "status": "PASS", "real_system": True, "command": contract[key],
            "exit_code": 0, "blocker": None, "artifact": str(log.relative_to(root)),
            "sha256": hashlib.sha256(log.read_bytes()).hexdigest(), "observed_at": now,
        })
    payload = {
        "schema_version": "3.2", "classification": "EXTERNAL_ACCEPTANCE_EVIDENCE_BUNDLE",
        "generated_at": now, "profile": "runtime",
        "command_contract_sha256": command_contract_sha256("runtime"),
        "real_target_explicitly_confirmed": True, "challenge": challenge,
        "environment": {"git_commit_sha": sha, "acceptance_environment_id_hash": "a"*64, "topology_hash": "b"*64},
        "evidence": rows, "groups": {"runtime": "PASS"}, "selected_all_pass": True,
    }
    if include_run_id:
        payload["run_id"] = run_id
    path = reports / "manifest_runtime.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    append_entry(reports / "evidence_ledger.json", manifest_sha256=hashlib.sha256(path.read_bytes()).hexdigest(), challenge_id=challenge["challenge_id"], git_commit_sha=sha, profile="runtime", root=root)
    return path


def test_strict_pass_requires_run_id(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("ACCEPTANCE_CHALLENGE_VERIFY_COMMAND", "true")
    result = verify_manifest(_runtime(tmp_path, inside_run_dir=True, include_run_id=False), root=tmp_path)
    assert "STRICT_PASS_RUN_ID_MISSING_OR_INVALID" in result["problems"]
    assert result["verified"] is False


def test_strict_pass_rejects_top_level_artifact_outside_run_dir(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("ACCEPTANCE_CHALLENGE_VERIFY_COMMAND", "true")
    result = verify_manifest(_runtime(tmp_path, inside_run_dir=False), root=tmp_path)
    assert any(p.startswith("ARTIFACT_OUTSIDE_IMMUTABLE_RUN_DIR:") for p in result["problems"])
    assert result["verified"] is False


def test_strict_pass_accepts_runner_shaped_run_artifacts(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("ACCEPTANCE_CHALLENGE_VERIFY_COMMAND", "true")
    result = verify_manifest(_runtime(tmp_path, inside_run_dir=True), root=tmp_path)
    assert result["verified"] is True
    assert result["groups"]["runtime"] == "PASS"
