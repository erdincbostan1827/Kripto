from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.release.acceptance_challenge import create_challenge, verify_challenge
from scripts.external_acceptance_runner import execute
from scripts.merge_external_acceptance import merge
from scripts.verify_external_acceptance import verify_manifest
from scripts.production_acceptance_handoff import build_handoff

PROFILES = (
    "locks", "runtime", "restart-drills", "supply-chain", "pitr", "ha", "worm",
    "testnet", "provenance", "campaigns",
)


def _run_cli(command: list[str]) -> dict[str, Any]:
    proc = subprocess.run(command, cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)
    return {"command": command, "exit_code": proc.returncode, "output": proc.stdout[-12000:]}


def _handoff_metadata(root: Path) -> dict[str, Any]:
    try:
        payload = build_handoff(root)
    except Exception as exc:
        payload = {
            "classification": "ACCEPTANCE_HANDOFF_NOT_ACCEPTANCE_EVIDENCE",
            "generated": False,
            "error_type": type(exc).__name__,
            "error": str(exc),
        }
    out = root / "reports" / "PRODUCTION_ACCEPTANCE_HANDOFF.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def orchestrate(*, confirm_real: bool, timeout: int = 300, profiles: tuple[str, ...] | None = None, reuse_current_challenge: bool = False) -> dict[str, Any]:
    reports = ROOT / "reports" / "external_acceptance"
    out = ROOT / "reports" / "PRODUCTION_ACCEPTANCE_ORCHESTRATION.json"
    selected_profiles = tuple(profiles or PROFILES)
    unknown_profiles = sorted(set(selected_profiles) - set(PROFILES))
    if unknown_profiles:
        raise ValueError(f"Unknown production acceptance profiles: {unknown_profiles}")
    if not selected_profiles:
        raise ValueError("At least one production acceptance profile must be selected")
    out.parent.mkdir(parents=True, exist_ok=True)
    if not confirm_real:
        payload = {
            "schema_version": "1.0",
            "classification": "PRODUCTION_ACCEPTANCE_ORCHESTRATION_PLAN_ONLY",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "truth_policy": "No external acceptance command is executed without --confirm-real-target.",
            "profiles": list(selected_profiles),
            "reuse_current_challenge": bool(reuse_current_challenge),
            "handoff": _handoff_metadata(ROOT),
            "executed": False,
            "production_ready": False,
            "blocker": "REAL_TARGET_NOT_EXPLICITLY_CONFIRMED",
        }
        out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return payload

    challenge_path = reports / "release_challenge.json"
    if reuse_current_challenge:
        checked = verify_challenge(challenge_path, root=ROOT, require_trust=True)
        if not checked.get("verified"):
            payload = {
                "schema_version": "1.1",
                "classification": "PRODUCTION_ACCEPTANCE_ORCHESTRATION_RESULT",
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "executed": False,
                "real_target_explicitly_confirmed": True,
                "profiles": list(selected_profiles),
                "reuse_current_challenge": True,
                "challenge_verification": checked,
                "production_ready": False,
                "blocker": "CURRENT_CHALLENGE_NOT_REUSABLE",
                "handoff": _handoff_metadata(ROOT),
            }
            out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            return payload
        challenge = {
            "challenge_id": checked.get("challenge_id"),
            "git_commit_sha": checked.get("git_commit_sha"),
            "schema_version": checked.get("schema_version"),
            "release_campaign_bound": checked.get("release_campaign_bound"),
            "sha256": checked.get("sha256"),
            "reused": True,
        }
    else:
        challenge = create_challenge(ROOT, challenge_path)
        challenge["reused"] = False
        checked = verify_challenge(challenge_path, root=ROOT, require_trust=True)
        if not checked.get("verified"):
            payload = {
                "schema_version": "1.2",
                "classification": "PRODUCTION_ACCEPTANCE_ORCHESTRATION_RESULT",
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "executed": False,
                "real_target_explicitly_confirmed": True,
                "profiles": list(selected_profiles),
                "reuse_current_challenge": False,
                "challenge": challenge,
                "challenge_verification": checked,
                "production_ready": False,
                "blocker": "NEW_CHALLENGE_NOT_VERIFIED",
                "handoff": _handoff_metadata(ROOT),
            }
            out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            return payload

    profile_results: dict[str, Any] = {}
    for profile in selected_profiles:
        result = execute(profile, confirm_real=True, timeout=timeout)
        profile_results[profile] = {
            "selected_all_pass": result.get("selected_all_pass", False),
            "groups": result.get("groups", {}),
            "manifest_sha256": result.get("manifest_sha256"),
            "immutable_manifest": result.get("immutable_manifest"),
            "run_id": result.get("run_id"),
        }

    merged = merge(root=ROOT)
    ledger_checkpoint = {"executed": False, "exit_code": None, "blocker": "MERGED_ACCEPTANCE_NOT_ALL_PASS"}
    if merged.get("selected_all_pass") is True:
        if os.getenv("LEDGER_CHECKPOINT_SIGN_COMMAND") and os.getenv("ACCEPTANCE_LEDGER_CHECKPOINT_VERIFY_COMMAND"):
            ledger_checkpoint = _run_cli(["bash", "scripts/external/ledger_checkpoint_sign_verify.sh"])
        else:
            ledger_checkpoint = {
                "executed": False,
                "exit_code": None,
                "blocker": "LEDGER_CHECKPOINT_SIGNING_OR_VERIFICATION_NOT_CONFIGURED",
            }
    verify = verify_manifest(reports / "manifest_all.json", root=ROOT)
    release_manifest = _run_cli([sys.executable, "scripts/generate_release_manifest.py"])
    release_gate = _run_cli([sys.executable, "scripts/release_gate.py"])
    dossier = _run_cli([sys.executable, "scripts/production_readiness_dossier.py"])
    production_ready = bool(
        merged.get("selected_all_pass")
        and verify.get("verified")
        and verify.get("selected_all_pass")
        and release_manifest["exit_code"] == 0
        and release_gate["exit_code"] == 0
    )
    payload = {
        "schema_version": "1.0",
        "classification": "PRODUCTION_ACCEPTANCE_ORCHESTRATION_RESULT",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "truth_policy": "production_ready=true requires every external profile, merged verifier, release-manifest generation, and release gate to succeed on the same release-bound challenge.",
        "executed": True,
        "real_target_explicitly_confirmed": True,
        "challenge": challenge,
        "challenge_verification": verify_challenge(reports / "release_challenge.json", root=ROOT, require_trust=True),
        "profiles": profile_results,
        "selected_profiles": list(selected_profiles),
        "reuse_current_challenge": bool(reuse_current_challenge),
        "merge": merged,
        "ledger_checkpoint": ledger_checkpoint,
        "verification": verify,
        "release_manifest": release_manifest,
        "release_gate": release_gate,
        "dossier": dossier,
        "handoff": _handoff_metadata(ROOT),
        "production_ready": production_ready,
    }
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def main() -> int:
    p = argparse.ArgumentParser(description="Fail-closed one-command production acceptance orchestrator")
    p.add_argument("--confirm-real-target", action="store_true")
    p.add_argument("--timeout", type=int, default=300)
    p.add_argument("--profiles", nargs="+", choices=PROFILES, help="Run only selected acceptance profiles under the current release campaign")
    p.add_argument("--reuse-current-challenge", action="store_true", help="Reuse only a fresh, verified challenge bound to the current Git SHA")
    args = p.parse_args()
    result = orchestrate(
        confirm_real=args.confirm_real_target,
        timeout=max(1, args.timeout),
        profiles=tuple(args.profiles) if args.profiles else None,
        reuse_current_challenge=args.reuse_current_challenge,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get("production_ready") is True else 2


if __name__ == "__main__":
    raise SystemExit(main())
