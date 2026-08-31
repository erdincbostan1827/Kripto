from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
REPORTS = ROOT / "reports" / "external_acceptance"

from backend.app.release.acceptance_challenge import verify_challenge
from backend.app.release.evidence_ledger import verify_ledger
from backend.app.release.acceptance_contract import GROUP_KEYS, DEFAULT_GROUP_TTL_HOURS, PROFILE_ORDER, PROFILE_TO_GROUPS, command_contract, command_contract_sha256
# centralized in backend.app.release.acceptance_contract
def _sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _relative_path_has_symlink_component(root: Path, relative: str) -> bool:
    rel = Path(relative)
    if rel.is_absolute() or ".." in rel.parts or not rel.parts:
        raise ValueError("acceptance artifact path must be a safe relative path")
    current = root
    for part in rel.parts:
        current = current / part
        if current.is_symlink():
            return True
    return False


def _strict_regular_artifact(root: Path, relative: str) -> Path:
    """Resolve an acceptance artifact without any symlink indirection.

    Production evidence is immutable-by-identity only when every path component
    from the configured root to the artifact is a direct filesystem entry.
    Checking only the final file would still allow a symlinked parent directory
    to redirect an otherwise regular artifact.
    """
    if _relative_path_has_symlink_component(root, relative):
        raise ValueError("acceptance artifact symlink component is not allowed")
    raw = root / relative
    resolved = raw.resolve()
    resolved.relative_to(root.resolve())
    if not resolved.is_file():
        raise ValueError("acceptance artifact is not a regular file")
    return resolved


def _parse_time(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def _verify_aggregate_source_profiles(payload: dict[str, Any], *, root: Path, max_age_hours: int) -> list[str]:
    problems: list[str] = []
    sources = payload.get("source_profiles")
    if not isinstance(sources, dict):
        return ["AGGREGATE_SOURCE_PROFILES_MISSING"]

    unexpected_profiles = sorted(set(sources) - set(PROFILE_ORDER))
    for source_profile in unexpected_profiles:
        problems.append(f"AGGREGATE_SOURCE_PROFILE_UNEXPECTED:{source_profile}")

    aggregate_environment = payload.get("environment") if isinstance(payload.get("environment"), dict) else {}
    aggregate_env_id = aggregate_environment.get("acceptance_environment_id_hash")
    aggregate_topology = aggregate_environment.get("topology_hash")
    expected_aggregate_rows: dict[str, dict[str, Any]] = {}

    for source_profile in PROFILE_ORDER:
        row = sources.get(source_profile)
        if not isinstance(row, dict):
            problems.append(f"AGGREGATE_SOURCE_PROFILE_MISSING:{source_profile}")
            continue
        reference = row.get("reference")
        expected_hash = row.get("sha256")
        if row.get("status") != "VERIFIED":
            problems.append(f"AGGREGATE_SOURCE_PROFILE_STATUS_INVALID:{source_profile}")
        if row.get("problems") not in (None, []):
            problems.append(f"AGGREGATE_SOURCE_PROFILE_PROBLEMS_NOT_EMPTY:{source_profile}")
        canonical_rel = f"reports/external_acceptance/manifest_{source_profile}.json"
        if reference != canonical_rel:
            problems.append(f"AGGREGATE_SOURCE_PROFILE_REFERENCE_INVALID:{source_profile}")
            continue
        try:
            source_path = _strict_regular_artifact(root, canonical_rel)
        except Exception:
            problems.append(f"AGGREGATE_SOURCE_PROFILE_ARTIFACT_INVALID:{source_profile}")
            continue
        if not isinstance(expected_hash, str) or _sha(source_path) != expected_hash:
            problems.append(f"AGGREGATE_SOURCE_PROFILE_HASH_MISMATCH:{source_profile}")
            continue
        try:
            source_doc = json.loads(source_path.read_text(encoding="utf-8"))
        except Exception:
            problems.append(f"AGGREGATE_SOURCE_PROFILE_JSON_INVALID:{source_profile}")
            continue
        source_environment = source_doc.get("environment") if isinstance(source_doc.get("environment"), dict) else {}
        if source_environment.get("acceptance_environment_id_hash") != aggregate_env_id:
            problems.append(f"AGGREGATE_SOURCE_PROFILE_ENVIRONMENT_MISMATCH:{source_profile}")
            continue
        if source_environment.get("topology_hash") != aggregate_topology:
            problems.append(f"AGGREGATE_SOURCE_PROFILE_TOPOLOGY_MISMATCH:{source_profile}")
            continue
        source_result = verify_manifest(source_path, root=root, max_age_hours=max_age_hours)
        if source_result.get("profile") != source_profile:
            problems.append(f"AGGREGATE_SOURCE_PROFILE_IDENTITY_MISMATCH:{source_profile}")
            continue
        if not source_result.get("verified"):
            problems.append(f"AGGREGATE_SOURCE_PROFILE_NOT_VERIFIED:{source_profile}")
            continue
        if not all(source_result.get("groups", {}).get(group) == "PASS" for group in PROFILE_TO_GROUPS[source_profile]):
            problems.append(f"AGGREGATE_SOURCE_PROFILE_GROUPS_NOT_PASS:{source_profile}")
            continue

        # Phase 167: the aggregate evidence rows are a materialized union of the
        # individually verified source-profile rows. Re-bind the exact row
        # metadata (command, observation time, status, artifact path/hash, etc.)
        # so a hand-edited aggregate cannot detach metadata from its source
        # profiles while still citing their valid manifest hashes.
        source_evidence = source_doc.get("evidence") if isinstance(source_doc.get("evidence"), list) else []
        source_rows: dict[str, dict[str, Any]] = {}
        duplicate_source_keys: set[str] = set()
        for source_row in source_evidence:
            if not isinstance(source_row, dict) or not isinstance(source_row.get("key"), str):
                continue
            key = source_row["key"]
            if key in source_rows:
                duplicate_source_keys.add(key)
            else:
                source_rows[key] = source_row
        for key in sorted(duplicate_source_keys):
            problems.append(f"AGGREGATE_SOURCE_PROFILE_DUPLICATE_EVIDENCE_KEY:{source_profile}:{key}")
        for group in PROFILE_TO_GROUPS[source_profile]:
            for key in GROUP_KEYS[group]:
                source_row = source_rows.get(key)
                if not isinstance(source_row, dict):
                    problems.append(f"AGGREGATE_SOURCE_PROFILE_EVIDENCE_MISSING:{source_profile}:{key}")
                    continue
                if key in expected_aggregate_rows and expected_aggregate_rows[key] != source_row:
                    problems.append(f"AGGREGATE_SOURCE_PROFILE_EVIDENCE_CONFLICT:{key}")
                    continue
                expected_aggregate_rows[key] = source_row

    aggregate_evidence = payload.get("evidence") if isinstance(payload.get("evidence"), list) else []
    aggregate_rows: dict[str, dict[str, Any]] = {}
    for aggregate_row in aggregate_evidence:
        if not isinstance(aggregate_row, dict) or not isinstance(aggregate_row.get("key"), str):
            continue
        key = aggregate_row["key"]
        if key not in aggregate_rows:
            aggregate_rows[key] = aggregate_row
    for key, expected_row in expected_aggregate_rows.items():
        observed_row = aggregate_rows.get(key)
        if observed_row is None:
            problems.append(f"AGGREGATE_EVIDENCE_ROW_MISSING:{key}")
        elif observed_row != expected_row:
            problems.append(f"AGGREGATE_EVIDENCE_ROW_MISMATCH:{key}")
    for key in sorted(set(aggregate_rows) - set(expected_aggregate_rows)):
        problems.append(f"AGGREGATE_EVIDENCE_ROW_UNEXPECTED:{key}")
    return problems


def verify_manifest(path: Path, *, root: Path = ROOT, max_age_hours: int = 168, group_ttl_hours: dict[str, int] | None = None) -> dict[str, Any]:
    problems: list[str] = []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"verified": False, "problems": [f"INVALID_JSON:{type(exc).__name__}"], "groups": {}, "manifest_sha256": _sha(path) if path.is_file() else None}

    if payload.get("classification") != "EXTERNAL_ACCEPTANCE_EVIDENCE_BUNDLE":
        problems.append("INVALID_CLASSIFICATION")
    if payload.get("real_target_explicitly_confirmed") is not True:
        problems.append("REAL_TARGET_NOT_CONFIRMED")

    profile = payload.get("profile")
    schema_version = str(payload.get("schema_version") or "")
    strict_command_contract = schema_version in {"3.2", "4.1"}
    if strict_command_contract:
        try:
            expected_contract_hash = command_contract_sha256(str(profile))
            expected_contract = command_contract(str(profile))
        except Exception:
            expected_contract_hash = None
            expected_contract = {}
            problems.append("COMMAND_CONTRACT_PROFILE_INVALID")
        if payload.get("command_contract_sha256") != expected_contract_hash:
            problems.append("COMMAND_CONTRACT_HASH_MISMATCH")
    else:
        expected_contract = {}

    challenge_doc = payload.get("challenge") if isinstance(payload.get("challenge"), dict) else {}
    current_challenge_path = root / "reports" / "external_acceptance" / "release_challenge.json"
    any_declared_group_pass = any((payload.get("groups") or {}).get(g) == "PASS" for g in GROUP_KEYS)
    # Phase 162: historical schemas remain readable for BLOCKED/NOT_TESTED
    # evidence, but can no longer assert production PASS without the current
    # command-contract binding introduced by schema 3.2/4.1.
    if any_declared_group_pass and not strict_command_contract:
        problems.append("LEGACY_SCHEMA_PASS_NOT_ALLOWED")
    # Phase 163: aggregate production PASS is a distinct contract.  Only the
    # merged schema 4.1 path carries the signed ledger checkpoint.  Conversely,
    # individual profile PASS must use schema 3.2; accepting 4.1 for a single
    # profile would blur the checkpoint boundary and weaken audit semantics.
    if any_declared_group_pass and profile == "all" and schema_version != "4.1":
        problems.append("AGGREGATE_PASS_REQUIRES_SCHEMA_4_1")
    if any_declared_group_pass and profile != "all" and schema_version != "3.2":
        problems.append("PROFILE_PASS_REQUIRES_SCHEMA_3_2")
    if any_declared_group_pass and path.is_symlink():
        problems.append("MANIFEST_SYMLINK_NOT_ALLOWED")

    strict_profile_run_dir: Path | None = None
    if any_declared_group_pass and profile != "all" and schema_version == "3.2":
        run_id = payload.get("run_id")
        if not isinstance(run_id, str) or not run_id or any(part in run_id for part in ("/", "\\", "..")):
            problems.append("STRICT_PASS_RUN_ID_MISSING_OR_INVALID")
        else:
            strict_profile_run_dir = (root / "reports" / "external_acceptance" / "runs" / run_id / str(profile)).resolve()

    current_challenge = verify_challenge(
        current_challenge_path, root=root, require_trust=True if any_declared_group_pass else False
    )
    if any_declared_group_pass:
        if not current_challenge.get("verified"):
            problems.append("CURRENT_RELEASE_CHALLENGE_NOT_VERIFIED")
        elif challenge_doc.get("challenge_id") != current_challenge.get("challenge_id"):
            problems.append("RELEASE_CHALLENGE_ID_MISMATCH")
        elif challenge_doc.get("sha256") != current_challenge.get("sha256"):
            problems.append("RELEASE_CHALLENGE_HASH_MISMATCH")

    expected_git = None
    try:
        expected_git = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        pass
    environment = payload.get("environment") if isinstance(payload.get("environment"), dict) else {}
    any_declared_pass = any((payload.get("groups") or {}).get(g) == "PASS" for g in GROUP_KEYS)
    if any_declared_pass:
        env_hash = environment.get("acceptance_environment_id_hash")
        topology_hash = environment.get("topology_hash")
        if not isinstance(env_hash, str) or len(env_hash) != 64:
            problems.append("ACCEPTANCE_ENVIRONMENT_IDENTITY_MISSING")
        if not isinstance(topology_hash, str) or len(topology_hash) != 64:
            problems.append("ACCEPTANCE_TOPOLOGY_HASH_MISSING")
    evidence_git = environment.get("git_commit_sha")
    if expected_git and evidence_git != expected_git:
        problems.append("GIT_COMMIT_MISMATCH")

    generated = _parse_time(payload.get("generated_at"))
    now = datetime.now(timezone.utc)
    if generated is None:
        problems.append("INVALID_GENERATED_AT")
    else:
        age = (now - generated.astimezone(timezone.utc)).total_seconds() / 3600
        if age < -1:
            problems.append("GENERATED_AT_IN_FUTURE")
        elif age > max_age_hours:
            problems.append("EVIDENCE_STALE")

    evidence_rows = payload.get("evidence")
    if not isinstance(evidence_rows, list):
        evidence_rows = []
        problems.append("EVIDENCE_NOT_LIST")

    evidence: dict[str, dict[str, Any]] = {}
    for row in evidence_rows:
        if not isinstance(row, dict) or not isinstance(row.get("key"), str):
            problems.append("INVALID_EVIDENCE_ROW")
            continue
        key = row["key"]
        if key in evidence:
            problems.append(f"DUPLICATE_EVIDENCE_KEY:{key}")
            continue
        evidence[key] = row
        if strict_command_contract:
            if key not in expected_contract:
                problems.append(f"COMMAND_CONTRACT_UNKNOWN_EVIDENCE_KEY:{key}")
            else:
                observed_command = row.get("command")
                if observed_command != expected_contract[key]:
                    problems.append(f"COMMAND_CONTRACT_COMMAND_MISMATCH:{key}")
        artifact = row.get("artifact")
        expected = row.get("sha256")
        if not isinstance(artifact, str) or not isinstance(expected, str):
            problems.append(f"MISSING_ARTIFACT_HASH:{key}")
            continue
        raw_artifact_path = root / artifact
        if strict_command_contract:
            try:
                if _relative_path_has_symlink_component(root, artifact):
                    problems.append(f"ARTIFACT_SYMLINK_NOT_ALLOWED:{key}")
                    continue
            except ValueError:
                problems.append(f"ARTIFACT_OUTSIDE_ROOT:{key}")
                continue
        artifact_path = raw_artifact_path.resolve()
        try:
            artifact_path.relative_to(root.resolve())
        except ValueError:
            problems.append(f"ARTIFACT_OUTSIDE_ROOT:{key}")
            continue
        if strict_profile_run_dir is not None:
            try:
                artifact_path.relative_to(strict_profile_run_dir)
            except ValueError:
                problems.append(f"ARTIFACT_OUTSIDE_IMMUTABLE_RUN_DIR:{key}")
                continue
        if not artifact_path.is_file():
            problems.append(f"ARTIFACT_MISSING:{key}")
        elif _sha(artifact_path) != expected:
            problems.append(f"ARTIFACT_HASH_MISMATCH:{key}")

    raw_groups = payload.get("groups") if isinstance(payload.get("groups"), dict) else {}
    effective_ttl = dict(DEFAULT_GROUP_TTL_HOURS)
    if group_ttl_hours:
        for group, hours in group_ttl_hours.items():
            if group in GROUP_KEYS and isinstance(hours, int) and hours > 0:
                effective_ttl[group] = hours
    verified_groups: dict[str, str] = {}
    for group, keys in GROUP_KEYS.items():
        declared = raw_groups.get(group, "NOT_TESTED")
        rows = [evidence.get(k) for k in keys]
        ttl_hours = effective_ttl[group]
        def _row_fresh(row: dict[str, Any] | None) -> bool:
            if not isinstance(row, dict):
                return False
            observed = _parse_time(row.get("observed_at"))
            if observed is None:
                return False
            hours_old = (now - observed.astimezone(timezone.utc)).total_seconds() / 3600
            return -1 <= hours_old <= ttl_hours
        group_ok = bool(rows) and all(
            isinstance(row, dict)
            and row.get("status") == "PASS"
            and row.get("real_system") is True
            and row.get("exit_code") == 0
            and row.get("blocker") is None
            and _row_fresh(row)
            for row in rows
        )
        if declared == "PASS":
            for key, row in zip(keys, rows):
                if isinstance(row, dict) and not _row_fresh(row):
                    problems.append(f"EVIDENCE_ROW_STALE_OR_INVALID_TIME:{group}:{key}")
        if declared == "PASS" and not group_ok:
            problems.append(f"FORGED_OR_INCOMPLETE_GROUP_PASS:{group}")
        verified_groups[group] = "PASS" if declared == "PASS" and group_ok else ("BLOCKED" if declared in {"PASS", "BLOCKED"} else "NOT_TESTED")

    # Phase 165: schema 4.1 claims to be a merge of individually verified
    # profile manifests. Re-prove that claim in the final verifier rather than
    # trusting merge metadata alone.
    if schema_version == "4.1" and profile == "all" and payload.get("selected_all_pass") is True:
        problems.extend(_verify_aggregate_source_profiles(payload, root=root, max_age_hours=max_age_hours))

    # Phase 159: a real strict aggregate PASS must be checkpointed after the
    # append-only ledger entry exists. The checkpoint is externally signed and
    # re-binds the ledger head to the trusted release challenge, Git identity,
    # acceptance environment and topology. Historical schemas remain parseable
    # without being promoted to this stricter production contract.
    if schema_version == "4.1" and profile == "all" and payload.get("selected_all_pass") is True:
        try:
            from backend.app.release.evidence_ledger_checkpoint import verify_ledger_checkpoint
            checkpoint = verify_ledger_checkpoint(
                root / "reports/external_acceptance/evidence_ledger_checkpoint.json",
                root=root,
                expected_environment=environment,
                require_external_trust=True,
            )
            if not checkpoint.get("verified"):
                problems.extend(f"EVIDENCE_LEDGER_CHECKPOINT:{p}" for p in checkpoint.get("problems", []))
        except Exception as exc:
            problems.append(f"EVIDENCE_LEDGER_CHECKPOINT_ERROR:{type(exc).__name__}")

    selected_all_pass = payload.get("selected_all_pass") is True
    if profile == "all":
        expected_all = all(v == "PASS" for v in verified_groups.values())
    else:
        mapping = {
            "locks": "dependency_locks_and_frontend_build", "runtime": "runtime", "supply-chain": "supply_chain",
            "pitr": "pitr", "ha": "ha", "worm": "worm", "restart-drills": "restart_drills", "testnet": "testnet", "provenance": "provenance",
        }
        if profile == "campaigns":
            expected_all = all(verified_groups.get(g) == "PASS" for g in ("private_stream", "paper_campaign", "live_shadow", "profitability"))
        else:
            g = mapping.get(profile)
            expected_all = bool(g and verified_groups.get(g) == "PASS")
    if selected_all_pass and not expected_all:
        problems.append("SELECTED_ALL_PASS_INCONSISTENT")

    if verified_groups.get("supply_chain") == "PASS":
        row = evidence.get("transferred_supply_chain_verification") or {}
        try:
            log_path = _strict_regular_artifact(root, str(row.get("artifact")))
            receipt = json.loads(log_path.read_text(encoding="utf-8").strip().splitlines()[-1])
            if receipt.get("schema_version") != "2.0":
                raise ValueError("transferred supply-chain schema 2.0 required")
            if receipt.get("classification") != "TRANSFERRED_CI_SUPPLY_CHAIN_ACCEPTANCE":
                raise ValueError("invalid transferred supply-chain classification")
            if receipt.get("verified") is not True:
                raise ValueError("transferred supply-chain verification not verified")
            if expected_git and receipt.get("git_commit_sha") != expected_git:
                raise ValueError("transferred supply-chain git mismatch")
            receipt_challenge = receipt.get("release_challenge") if isinstance(receipt.get("release_challenge"), dict) else {}
            if receipt_challenge.get("challenge_id") != challenge_doc.get("challenge_id") or receipt_challenge.get("sha256") != challenge_doc.get("sha256"):
                raise ValueError("transferred supply-chain release challenge mismatch")
            receipt_environment = receipt.get("environment") if isinstance(receipt.get("environment"), dict) else {}
            if receipt_environment.get("acceptance_environment_id_hash") != environment.get("acceptance_environment_id_hash"):
                raise ValueError("transferred supply-chain environment mismatch")
            if receipt_environment.get("topology_hash") != environment.get("topology_hash"):
                raise ValueError("transferred supply-chain topology mismatch")
            for key in ("transfer_manifest_sha256", "scanner_receipt_sha256", "sbom_sha256", "license_report_sha256", "provenance_sha256"):
                value = receipt.get(key)
                if not isinstance(value, str) or len(value) != 64 or any(c not in "0123456789abcdef" for c in value.lower()):
                    raise ValueError(f"invalid transferred supply-chain hash: {key}")
        except Exception as exc:
            problems.append(f"SUPPLY_CHAIN_SUBARTIFACT_INVALID:{type(exc).__name__}")
            verified_groups["supply_chain"] = "BLOCKED"

    # PITR/HA/WORM wrappers must bind the exact semantic evidence JSON into the outer bundle.
    drill_specs = {"pitr": "pitr_drill", "ha": "ha_drill", "worm": "worm_storage"}
    for group, evidence_key in drill_specs.items():
        if verified_groups.get(group) != "PASS":
            continue
        row = evidence.get(evidence_key) or {}
        try:
            log_path = _strict_regular_artifact(root, str(row.get("artifact")))
            receipt = json.loads(log_path.read_text(encoding="utf-8").strip().splitlines()[-1])
            nested_rel = receipt["evidence_artifact"]
            nested_path = _strict_regular_artifact(root, nested_rel)
            if _sha(nested_path) != receipt.get("evidence_sha256"):
                raise ValueError("nested drill evidence hash mismatch")
            from backend.app.release.drill_evidence import verify_ha_evidence, verify_restore_evidence, verify_worm_evidence
            verifier = {"pitr": verify_restore_evidence, "ha": verify_ha_evidence, "worm": verify_worm_evidence}[group]
            verifier(nested_path, root=root, max_age_hours=effective_ttl[group], expected_environment=payload.get("environment") if isinstance(payload.get("environment"), dict) else None)
        except Exception as exc:
            problems.append(f"DRILL_SUBARTIFACT_INVALID:{group}:{type(exc).__name__}")
            verified_groups[group] = "BLOCKED"

    if verified_groups.get("restart_drills") == "PASS":
        row = evidence.get("restart_semantic_evidence") or {}
        try:
            log_path = _strict_regular_artifact(root, str(row.get("artifact")))
            receipt = json.loads(log_path.read_text(encoding="utf-8").strip().splitlines()[-1])
            nested_rel = receipt["evidence_artifact"]
            nested_path = _strict_regular_artifact(root, nested_rel)
            if _sha(nested_path) != receipt.get("evidence_sha256"):
                raise ValueError("nested restart evidence hash mismatch")
            from backend.app.release.runtime_restart_evidence import verify_restart_evidence
            result = verify_restart_evidence(nested_path, root=root, max_age_hours=effective_ttl.get("restart_drills", max_age_hours), expected_environment=payload.get("environment") if isinstance(payload.get("environment"), dict) else None)
            if not result.get("verified"):
                raise ValueError("restart semantic evidence verification failed")
        except Exception as exc:
            problems.append(f"RESTART_SUBARTIFACT_INVALID:{type(exc).__name__}")
            verified_groups["restart_drills"] = "BLOCKED"

    campaign_specs = {
        "private_stream": ("private_stream_evidence", "private-stream"),
        "paper_campaign": ("paper_campaign_evidence", "paper"),
        "live_shadow": ("live_shadow_evidence", "live-shadow"),
        "profitability": ("profitability_evidence", "profitability"),
    }
    for group, (evidence_key, kind) in campaign_specs.items():
        if verified_groups.get(group) != "PASS":
            continue
        row = evidence.get(evidence_key) or {}
        try:
            log_path = _strict_regular_artifact(root, str(row.get("artifact")))
            receipt = json.loads(log_path.read_text(encoding="utf-8").strip().splitlines()[-1])
            nested_rel = receipt["evidence_artifact"]
            nested_path = _strict_regular_artifact(root, nested_rel)
            if _sha(nested_path) != receipt.get("sha256"):
                raise ValueError("nested campaign evidence hash mismatch")
            from backend.app.release.campaign_acceptance import verify_campaign_evidence
            result = verify_campaign_evidence(nested_path, kind=kind, root=root, max_age_hours=effective_ttl[group], strict_external=True, expected_environment=payload.get("environment") if isinstance(payload.get("environment"), dict) else None)
            if not result.get("verified"):
                raise ValueError("campaign evidence semantic verification failed")
        except Exception as exc:
            problems.append(f"CAMPAIGN_SUBARTIFACT_INVALID:{group}:{type(exc).__name__}")
            verified_groups[group] = "BLOCKED"

    if verified_groups.get("provenance") == "PASS":
        row = evidence.get("artifact_sign_verify") or {}
        try:
            log_path = _strict_regular_artifact(root, str(row.get("artifact")))
            receipt = json.loads(log_path.read_text(encoding="utf-8").strip().splitlines()[-1])
            nested_rel = receipt["evidence_artifact"]
            nested_path = _strict_regular_artifact(root, nested_rel)
            if receipt.get("sha256") != _sha(nested_path):
                raise ValueError("signature evidence hash mismatch")
            from backend.app.release.provenance_signature_evidence import verify_provenance_signature_evidence
            signature_result = verify_provenance_signature_evidence(
                nested_path,
                root=root,
                max_age_hours=effective_ttl["provenance"],
                strict_external=True,
                expected_environment=payload.get("environment") if isinstance(payload.get("environment"), dict) else None,
            )
            if not signature_result.get("verified"):
                raise ValueError("signature evidence semantic verification failed")
        except Exception as exc:
            problems.append(f"PROVENANCE_SIGNATURE_SUBARTIFACT_INVALID:{type(exc).__name__}")
            verified_groups["provenance"] = "BLOCKED"

    provenance = None
    if verified_groups.get("provenance") == "PASS":
        row = evidence.get("ci_provenance_capture") or {}
        log_rel = row.get("artifact")
        try:
            log_text = _strict_regular_artifact(root, str(log_rel)).read_text(encoding="utf-8")
            receipt = json.loads(log_text.strip().splitlines()[-1])
            prov_rel = receipt["artifact"]
            prov_path = _strict_regular_artifact(root, prov_rel)
            if _sha(prov_path) != receipt.get("sha256"):
                raise ValueError("nested provenance hash mismatch")
            provenance = json.loads(prov_path.read_text(encoding="utf-8"))
            if provenance.get("classification") != "REAL_CI_BUILD_PROVENANCE":
                raise ValueError("invalid provenance classification")
            if expected_git and provenance.get("git_commit_sha") != expected_git:
                raise ValueError("provenance git mismatch")
            required = ("ci_run_id", "dependency_lock_hash", "frontend_lock_hash", "sbom_hash", "license_report_hash", "supply_chain_verification_hash", "scanner_image_digest_manifest_hash", "container_digest", "frontend_artifact_hash")
            if any(not provenance.get(k) for k in required):
                raise ValueError("missing provenance fields")
            scanner_receipt = _strict_regular_artifact(root, "reports/external_acceptance/scanner_image_digests.json")
            if _sha(scanner_receipt) != provenance.get("scanner_image_digest_manifest_hash"):
                raise ValueError("scanner digest receipt hash mismatch")
            from scripts.external.verify_scanner_image_digests import verify as verify_scanner_image_digests
            scanner_verification = verify_scanner_image_digests(scanner_receipt)
            if not scanner_verification.get("verified"):
                raise ValueError("scanner digest receipt semantic verification failed")
        except Exception as exc:
            problems.append(f"PROVENANCE_SUBARTIFACT_INVALID:{type(exc).__name__}")
            verified_groups["provenance"] = "BLOCKED"

    if any(v == "PASS" for v in verified_groups.values()):
        ledger_path = root / "reports" / "external_acceptance" / "evidence_ledger.json"
        ledger = verify_ledger(ledger_path)
        if not ledger.get("verified"):
            problems.extend(f"EVIDENCE_LEDGER:{p}" for p in ledger.get("problems", []))
        else:
            try:
                ledger_doc = json.loads(ledger_path.read_text(encoding="utf-8"))
                manifest_hash = _sha(path)
                challenge_id = challenge_doc.get("challenge_id")
                expected_ledger_profile = "all-merged" if profile == "all" else profile
                expected_row = any(
                    row.get("manifest_sha256") == manifest_hash
                    and row.get("challenge_id") == challenge_id
                    and row.get("git_commit_sha") == expected_git
                    and row.get("profile") == expected_ledger_profile
                    for row in ledger_doc.get("entries", [])
                    if isinstance(row, dict)
                )
                if not expected_row:
                    problems.append("EVIDENCE_LEDGER_MANIFEST_BINDING_MISSING")
            except Exception as exc:
                problems.append(f"EVIDENCE_LEDGER_READ_FAILED:{type(exc).__name__}")

    return {
        "verified": not problems,
        "problems": problems,
        "groups": verified_groups,
        "profile": profile,
        "real_target_confirmed": payload.get("real_target_explicitly_confirmed") is True,
        "selected_all_pass": bool(selected_all_pass and expected_all and not problems),
        "manifest_sha256": _sha(path),
        "effective_group_ttl_hours": effective_ttl,
        "provenance": provenance,
    }


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description="Verify external acceptance evidence hashes and fail closed on forged PASS claims")
    parser.add_argument("manifest", nargs="?", default=str(REPORTS / "manifest_all.json"))
    parser.add_argument("--max-age-hours", type=int, default=168)
    parser.add_argument("--group-ttl", action="append", default=[], metavar="GROUP=HOURS")
    args = parser.parse_args()
    overrides: dict[str, int] = {}
    for raw in args.group_ttl:
        try:
            group, hours = raw.split("=", 1)
            hours_i = int(hours)
        except Exception:
            parser.error(f"invalid --group-ttl value: {raw}")
        if group not in GROUP_KEYS or hours_i < 1:
            parser.error(f"invalid --group-ttl value: {raw}")
        overrides[group] = hours_i
    result = verify_manifest(Path(args.manifest), max_age_hours=max(1, args.max_age_hours), group_ttl_hours=overrides)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["verified"] and result["selected_all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
