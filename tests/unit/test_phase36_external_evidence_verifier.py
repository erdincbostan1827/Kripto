from __future__ import annotations

import json
import subprocess
from dataclasses import asdict
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path

import scripts.verify_external_acceptance as verifier
from backend.app.release.acceptance_challenge import create_challenge
from backend.app.release.evidence_ledger import append_entry


def _write_bundle(root: Path, *, tamper: bool = False, forged_group: bool = False, wrong_git: bool = False, ledger_profile: str = "all-merged") -> Path:
    if not (root / ".git").exists():
        subprocess.run(["git", "init", "-q"], cwd=root, check=True)
        subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=root, check=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=root, check=True)
        (root / "seed.txt").write_text("seed\n")
        subprocess.run(["git", "add", "seed.txt"], cwd=root, check=True)
        subprocess.run(["git", "commit", "-q", "-m", "seed"], cwd=root, check=True)
    git_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    reports = root / "reports" / "external_acceptance"
    reports.mkdir(parents=True)
    challenge_path = reports / "release_challenge.json"
    challenge = create_challenge(root, challenge_path)
    evidence = []
    for group, keys in verifier.GROUP_KEYS.items():
        for key in keys:
            log = reports / f"{key}.log"
            if key == "transferred_supply_chain_verification":
                log.write_text(json.dumps({
                    "schema_version": "2.0",
                    "classification": "TRANSFERRED_CI_SUPPLY_CHAIN_ACCEPTANCE",
                    "verified": True,
                    "git_commit_sha": git_sha,
                    "release_challenge": {"challenge_id": challenge["challenge_id"], "sha256": challenge["sha256"]},
                    "environment": {"acceptance_environment_id_hash": "a" * 64, "topology_hash": "b" * 64},
                    "problems": [],
                    "transfer_manifest_sha256": "4" * 64,
                    "scanner_receipt_sha256": "5" * 64,
                    "sbom_sha256": "6" * 64,
                    "license_report_sha256": "7" * 64,
                    "provenance_sha256": "8" * 64,
                }) + "\n", encoding="utf-8")
            elif key == "ci_provenance_capture":
                scanner_receipt = reports / "scanner_image_digests.json"
                scanner_receipt.write_text(json.dumps({
                    "schema_version": "1.0",
                    "classification": "CI_SCANNER_IMAGE_DIGEST_RECEIPT",
                    "scanners": {
                        "gitleaks": {"requested_image": "ghcr.io/gitleaks/gitleaks:v8.28.0", "resolved_digest": "ghcr.io/gitleaks/gitleaks@sha256:" + "1" * 64},
                        "trivy": {"requested_image": "aquasec/trivy:0.65.0", "resolved_digest": "aquasec/trivy@sha256:" + "2" * 64},
                        "syft": {"requested_image": "anchore/syft:v1.32.0", "resolved_digest": "anchore/syft@sha256:" + "3" * 64},
                    },
                }), encoding="utf-8")
                prov = reports / "provenance.json"
                prov.write_text(json.dumps({
                    "classification": "REAL_CI_BUILD_PROVENANCE", "git_commit_sha": git_sha, "ci_run_id": "42",
                    "dependency_lock_hash": "a" * 64, "frontend_lock_hash": "b" * 64, "sbom_hash": "c" * 64,
                    "license_report_hash": "f" * 64, "supply_chain_verification_hash": "1" * 64,
                    "scanner_image_digest_manifest_hash": sha256(scanner_receipt.read_bytes()).hexdigest(),
                    "container_digest": "repo@sha256:" + "d" * 64, "frontend_artifact_hash": "e" * 64,
                }), encoding="utf-8")
                log.write_text(json.dumps({"status": "PASS", "artifact": str(prov.relative_to(root)),
                                           "sha256": sha256(prov.read_bytes()).hexdigest()}) + "\n", encoding="utf-8")
            elif key == "artifact_sign_verify":
                prov = reports / "provenance.json"
                if not prov.exists():
                    prov.write_text(json.dumps({"classification": "REAL_CI_BUILD_PROVENANCE", "git_commit_sha": git_sha}), encoding="utf-8")
                sig = reports / "provenance.sig"
                sig.write_text("signature", encoding="utf-8")
                nested = reports / "provenance_signature_verification.json"
                nested.write_text(json.dumps({
                    "schema_version": "2.0",
                    "classification": "REAL_PROVENANCE_SIGNATURE_VERIFICATION",
                    "observed_at": datetime.now(timezone.utc).isoformat(),
                    "git_commit_sha": git_sha,
                    "real_system": True,
                    "executed": True,
                    "signature_verified": True,
                    "signer_identity": "test-ci",
                    "signature_mechanism": "test-detached",
                    "release_challenge": {"challenge_id": challenge["challenge_id"], "sha256": challenge["sha256"]},
                    "environment": {"acceptance_environment_id_hash": "a" * 64, "topology_hash": "b" * 64},
                    "provenance_artifact": str(prov.relative_to(root)),
                    "provenance_sha256": sha256(prov.read_bytes()).hexdigest(),
                    "signature_artifact": str(sig.relative_to(root)),
                    "signature_sha256": sha256(sig.read_bytes()).hexdigest(),
                }), encoding="utf-8")
                log.write_text(json.dumps({"verified": True, "evidence_artifact": str(nested.relative_to(root)),
                                           "sha256": sha256(nested.read_bytes()).hexdigest()}) + "\n", encoding="utf-8")
            elif key in {"private_stream_evidence", "paper_campaign_evidence", "live_shadow_evidence", "profitability_evidence"}:
                source = reports / f"{key}.source.ndjson"
                source.write_text('{"event":"real"}\n', encoding="utf-8")
                common = {
                    "schema_version": "1.0",
                    "generated_at": datetime.now(timezone.utc).isoformat(), "git_commit_sha": git_sha,
                    "real_system": True, "executed": True,
                    "release_challenge": {"challenge_id": challenge["challenge_id"], "sha256": challenge["sha256"]},
                    "environment": {"acceptance_environment_id_hash": "a" * 64, "topology_hash": "b" * 64},
                    "source_artifacts": [{"path": str(source.relative_to(root)), "sha256": sha256(source.read_bytes()).hexdigest()}],
                }
                if key == "private_stream_evidence":
                    doc = {**common, "classification": "CREDENTIALED_PRIVATE_STREAM_ACCEPTANCE", "metrics": {
                        "credentialed_testnet": True, "auth_lifecycle_passed": True, "reconnect_passed": True,
                        "rest_reconciliation_passed": True, "duplicate_event_idempotency_passed": True,
                        "out_of_order_protection_passed": True, "secrets_redacted": True, "observed_events": 10}}
                elif key == "paper_campaign_evidence":
                    doc = {**common, "classification": "REAL_MARKET_PAPER_CAMPAIGN_ACCEPTANCE", "metrics": {
                        "effective_sample_size": 120, "calendar_days": 31, "market_regimes": ["trend", "range"],
                        "long_examples": 30, "exit_examples": 30, "short_examples": 0, "active_market_type": "SPOT",
                        "cost_stress_passed": True, "latency_stress_passed": True, "independent_oos_passed": True,
                        "execution_divergence_bps": 10, "real_market_data": True}}
                elif key == "live_shadow_evidence":
                    doc = {**common, "classification": "LIVE_SHADOW_CAMPAIGN_ACCEPTANCE", "metrics": {
                        "real_market_data": True, "calendar_days": 7, "observations": 150, "real_orders_submitted": 0,
                        "exchange_submit_calls": 0, "kill_switch_tested": True, "reconciliation_passed": True}}
                else:
                    doc = {**common, "classification": "REAL_PIT_PROFITABILITY_ACCEPTANCE", "metrics": {
                        "real_point_in_time_data": True, "independent_oos": True, "leakage_checks_passed": True,
                        "cost_stress_passed": True, "survivorship_controls_passed": True, "effective_sample_size": 180,
                        "net_expectancy_bps": 5, "bootstrap_ci_lower_bps": 1, "probabilistic_sharpe_ratio": 0.97}}
                nested = reports / f"{key}.json"
                nested.write_text(json.dumps(doc), encoding="utf-8")
                log.write_text(json.dumps({"verified": True, "evidence_artifact": str(nested.relative_to(root)),
                                           "sha256": sha256(nested.read_bytes()).hexdigest()}) + "\n", encoding="utf-8")
            elif key == "restart_semantic_evidence":
                sublog = reports / "restart_semantic.source.log"
                sublog.write_text("state-before=42\nstate-after=42\nreconciled=12\n", encoding="utf-8")
                restart_doc = {
                    "schema_version": "1.0", "classification": "REAL_RUNTIME_RESTART_ACCEPTANCE",
                    "generated_at": datetime.now(timezone.utc).isoformat(), "git_commit_sha": git_sha,
                    "real_system": True, "executed": True,
                    "release_challenge": {"challenge_id": challenge["challenge_id"], "sha256": challenge["sha256"]},
                    "environment": {"acceptance_environment_id_hash": "a" * 64, "topology_hash": "b" * 64},
                    "source_artifacts": [{"path": str(sublog.relative_to(root)), "sha256": sha256(sublog.read_bytes()).hexdigest()}],
                    "metrics": {
                        "redis_restart_executed": True, "postgres_restart_executed": True,
                        "state_persisted_before_restart": True, "state_persisted_after_restart": True,
                        "services_reconnected": True, "application_reconciliation_passed": True,
                        "no_duplicate_orders": True, "risk_fail_closed_during_outage": True,
                        "healthy_recovery": True, "reconciled_records": 12, "duplicate_orders_detected": 0,
                    },
                }
                nested = reports / "restart_semantic.json"
                nested.write_text(json.dumps(restart_doc), encoding="utf-8")
                log.write_text(json.dumps({"status": "PASS", "evidence_artifact": str(nested.relative_to(root)),
                                           "evidence_sha256": sha256(nested.read_bytes()).hexdigest()}) + "\n", encoding="utf-8")
            elif key in {"pitr_drill", "ha_drill", "worm_storage"}:
                kind = {"pitr_drill": "PITR_RESTORE", "ha_drill": "HA_FAILOVER", "worm_storage": "WORM_STORAGE"}[key]
                sublog = reports / f"{key}.evidence.log"
                sublog.write_text("real semantic drill evidence\n", encoding="utf-8")
                drill = {
                    "schema_version": "2.0",
                    "classification": "REAL_EXTERNAL_ACCEPTANCE_DRILL", "drill_kind": kind, "real_system": True,
                    "observed_at": datetime.now(timezone.utc).isoformat(), "git_commit_sha": git_sha,
                    "release_challenge": {"challenge_id": challenge["challenge_id"], "sha256": challenge["sha256"]},
                    "environment": {"acceptance_environment_id_hash": "a" * 64, "topology_hash": "b" * 64},
                    "artifacts": [{"path": str(sublog.relative_to(root)), "sha256": sha256(sublog.read_bytes()).hexdigest()}],
                }
                if key == "pitr_drill":
                    drill.update({k: True for k in ("isolated_environment", "backup_or_pitr_restored", "schema_validated", "referential_integrity_validated", "checksum_validated", "read_only_smoke_passed", "result_reported")})
                elif key == "ha_drill":
                    drill.update({k: True for k in ("active_process_kill_passed", "stale_leader_fencing_passed", "private_stream_reconciliation_passed", "host_loss_simulation_passed", "db_failover_passed", "network_partition_passed")})
                    drill.update(redis_ha_applicable=False, redis_failover_passed=False)
                else:
                    drill.update({k: True for k in ("append_only_verified", "retention_lock_verified", "delete_before_retention_denied", "overwrite_denied", "readback_verified")})
                    drill.update(provider="test-provider", retention_policy_reference="policy-1")
                drill_path = reports / f"{key}.json"
                drill_path.write_text(json.dumps(drill), encoding="utf-8")
                log.write_text(json.dumps({"status": "PASS", "evidence_artifact": str(drill_path.relative_to(root)),
                                           "evidence_sha256": sha256(drill_path.read_bytes()).hexdigest()}) + "\n", encoding="utf-8")
            else:
                log.write_text(f"real evidence for {key}\n", encoding="utf-8")
            digest = sha256(log.read_bytes()).hexdigest()
            evidence.append({
                "key": key, "status": "PASS", "real_system": True, "command": ["tool"], "exit_code": 0,
                "blocker": None, "artifact": str(log.relative_to(root)), "sha256": digest,
                "observed_at": datetime.now(timezone.utc).isoformat(),
            })
    groups = {g: "PASS" for g in verifier.GROUP_KEYS}
    if forged_group:
        key = verifier.GROUP_KEYS["runtime"][0]
        next(e for e in evidence if e["key"] == key)["status"] = "BLOCKED"
    manifest = reports / "manifest_all.json"
    manifest.write_text(json.dumps({
        "schema_version": "3.0", "generated_at": datetime.now(timezone.utc).isoformat(),
        "classification": "EXTERNAL_ACCEPTANCE_EVIDENCE_BUNDLE", "profile": "all",
        "real_target_explicitly_confirmed": True, "challenge": challenge,
        "environment": {"git_commit_sha": "0" * 40 if wrong_git else git_sha, "acceptance_environment_id_hash": "a" * 64, "topology_hash": "b" * 64},
        "evidence": evidence, "groups": groups, "selected_all_pass": True,
    }), encoding="utf-8")
    append_entry(reports / "evidence_ledger.json", manifest_sha256=sha256(manifest.read_bytes()).hexdigest(),
                 challenge_id=challenge["challenge_id"], git_commit_sha=git_sha, profile=ledger_profile)
    if tamper:
        (reports / f"{verifier.GROUP_KEYS['runtime'][0]}.log").write_text("tampered\n", encoding="utf-8")
    return manifest


def test_legacy_real_bundle_pass_is_deprecated(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("ACCEPTANCE_CHALLENGE_VERIFY_COMMAND", "true")
    result = verifier.verify_manifest(_write_bundle(tmp_path), root=tmp_path)
    assert result["verified"] is False
    assert result["selected_all_pass"] is False
    assert "LEGACY_SCHEMA_PASS_NOT_ALLOWED" in result["problems"]



def test_aggregate_manifest_requires_all_merged_ledger_profile(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("ACCEPTANCE_CHALLENGE_VERIFY_COMMAND", "true")
    manifest = _write_bundle(tmp_path, ledger_profile="runtime")
    result = verifier.verify_manifest(manifest, root=tmp_path)
    assert result["verified"] is False
    assert "EVIDENCE_LEDGER_MANIFEST_BINDING_MISSING" in result["problems"]

def test_tampered_artifact_hash_fails_closed(tmp_path: Path):
    result = verifier.verify_manifest(_write_bundle(tmp_path, tamper=True), root=tmp_path)
    assert result["verified"] is False
    assert result["selected_all_pass"] is False
    assert any(p.startswith("ARTIFACT_HASH_MISMATCH:") for p in result["problems"])


def test_forged_group_pass_fails_closed(tmp_path: Path):
    result = verifier.verify_manifest(_write_bundle(tmp_path, forged_group=True), root=tmp_path)
    assert result["verified"] is False
    assert result["groups"]["runtime"] == "BLOCKED"
    assert "FORGED_OR_INCOMPLETE_GROUP_PASS:runtime" in result["problems"]


def test_unconfirmed_real_target_never_verifies(tmp_path: Path):
    manifest = _write_bundle(tmp_path)
    payload = json.loads(manifest.read_text())
    payload["real_target_explicitly_confirmed"] = False
    manifest.write_text(json.dumps(payload), encoding="utf-8")
    result = verifier.verify_manifest(manifest, root=tmp_path)
    assert result["verified"] is False
    assert "REAL_TARGET_NOT_CONFIRMED" in result["problems"]


def test_different_git_commit_bundle_is_rejected(tmp_path: Path):
    result = verifier.verify_manifest(_write_bundle(tmp_path, wrong_git=True), root=tmp_path)
    assert result["verified"] is False
    assert "GIT_COMMIT_MISMATCH" in result["problems"]
