from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import uuid
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.release.acceptance_challenge import verify_challenge
from backend.app.release.campaign_acceptance import verify_campaign_evidence
from scripts.external.stage_campaign_evidence_bundle import verify_and_stage

RECEIPT = ROOT / "reports" / "phase251" / "FINAL_CAMPAIGN_HANDOFF_VERIFICATION.json"
CAMPAIGNS = {
    "private-stream": "reports/external_acceptance/campaign/private_stream.json",
    "paper": "reports/external_acceptance/campaign/paper_campaign.json",
    "live-shadow": "reports/external_acceptance/campaign/live_shadow.json",
    "profitability": "reports/external_acceptance/campaign/profitability.json",
}


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _outside_root(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return False
    except ValueError:
        return True


def _write_receipt(payload: dict[str, Any], output: Path = RECEIPT) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def handoff(
    *,
    bundle: Path,
    expected_sha256: str,
    expected_candidate: str,
    expected_environment_id: str,
    expected_topology_hash: str,
    root: Path = ROOT,
    max_age_hours: int = 168,
) -> dict[str, Any]:
    candidate = expected_candidate.strip().lower()
    expected_digest = expected_sha256.strip().lower()
    topology = expected_topology_hash.strip().lower()
    environment_id = expected_environment_id.strip()
    problems: list[str] = []

    if len(candidate) != 40 or any(ch not in "0123456789abcdef" for ch in candidate):
        problems.append("EXPECTED_CANDIDATE_SHA_INVALID")
    if len(expected_digest) != 64 or any(ch not in "0123456789abcdef" for ch in expected_digest):
        problems.append("EXPECTED_BUNDLE_SHA256_INVALID")
    if not environment_id:
        problems.append("EXPECTED_ACCEPTANCE_ENVIRONMENT_ID_MISSING")
    if len(topology) != 64 or any(ch not in "0123456789abcdef" for ch in topology):
        problems.append("EXPECTED_TOPOLOGY_HASH_INVALID")
    if not bundle.is_absolute():
        problems.append("BUNDLE_PATH_MUST_BE_ABSOLUTE")
    if bundle.is_file() and not _outside_root(bundle, root):
        problems.append("BUNDLE_MUST_BE_OUTSIDE_REPOSITORY")
    if not bundle.is_file():
        problems.append("BUNDLE_FILE_MISSING")
    if problems:
        return {"verified": False, "problems": problems, "live_enabled": False, "production_ready": False}

    actual_digest = _sha256_file(bundle)
    if actual_digest != expected_digest:
        return {
            "verified": False,
            "bundle_sha256": actual_digest,
            "problems": ["BUNDLE_SHA256_MISMATCH"],
            "live_enabled": False,
            "production_ready": False,
        }

    staging_root = root / "reports" / "phase251" / "staging" / f"{expected_digest}-{uuid.uuid4().hex}"
    if staging_root.exists():
        return {"verified": False, "problems": ["STAGING_ROOT_ALREADY_EXISTS"], "live_enabled": False, "production_ready": False}
    staging_root.mkdir(parents=True, exist_ok=False)

    transfer = verify_and_stage(
        bundle,
        expected_sha256=expected_digest,
        expected_candidate=candidate,
        root=staging_root,
    )
    if transfer.get("verified") is not True:
        return {
            "verified": False,
            "bundle_sha256": actual_digest,
            "transfer": transfer,
            "problems": ["CAMPAIGN_BUNDLE_TRANSFER_NOT_VERIFIED"],
            "live_enabled": False,
            "production_ready": False,
        }
    if transfer.get("acceptance_environment_id") != environment_id:
        return {
            "verified": False,
            "bundle_sha256": actual_digest,
            "transfer": transfer,
            "problems": ["CAMPAIGN_ENVIRONMENT_ID_MISMATCH"],
            "live_enabled": False,
            "production_ready": False,
        }
    if str(transfer.get("topology_hash", "")).lower() != topology:
        return {
            "verified": False,
            "bundle_sha256": actual_digest,
            "transfer": transfer,
            "problems": ["CAMPAIGN_TOPOLOGY_HASH_MISMATCH"],
            "live_enabled": False,
            "production_ready": False,
        }

    staged_acceptance = staging_root / "reports" / "external_acceptance"
    staged_files = sorted(path for path in staged_acceptance.rglob("*") if path.is_file())
    if not staged_files:
        return {"verified": False, "problems": ["STAGED_CAMPAIGN_EVIDENCE_EMPTY"], "live_enabled": False, "production_ready": False}

    promotions: list[tuple[Path, Path]] = []
    for source in staged_files:
        rel = source.relative_to(staging_root)
        target = (root / rel).resolve()
        target.relative_to(root.resolve())
        if target.exists():
            return {
                "verified": False,
                "problems": [f"PROMOTION_DESTINATION_ALREADY_EXISTS:{rel.as_posix()}"],
                "live_enabled": False,
                "production_ready": False,
            }
        promotions.append((source, target))

    for source, target in promotions:
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)

    challenge = verify_challenge(
        root / "reports" / "external_acceptance" / "release_challenge.json",
        root=root,
        require_trust=True,
    )
    if challenge.get("verified") is not True or challenge.get("trust_verified") is not True:
        return {
            "verified": False,
            "bundle_sha256": actual_digest,
            "challenge": challenge,
            "problems": ["PROMOTED_CHALLENGE_TRUST_NOT_VERIFIED"],
            "live_enabled": False,
            "production_ready": False,
        }
    if str(challenge.get("git_commit_sha", "")).lower() != candidate:
        return {
            "verified": False,
            "bundle_sha256": actual_digest,
            "challenge": challenge,
            "problems": ["PROMOTED_CHALLENGE_CANDIDATE_MISMATCH"],
            "live_enabled": False,
            "production_ready": False,
        }

    environment_binding = {
        "acceptance_environment_id_hash": hashlib.sha256(environment_id.encode()).hexdigest(),
        "topology_hash": topology,
    }
    campaign_results: dict[str, Any] = {}
    for kind, rel in CAMPAIGNS.items():
        result = verify_campaign_evidence(
            root / rel,
            kind=kind,
            root=root,
            max_age_hours=max(1, max_age_hours),
            strict_external=True,
            expected_environment=environment_binding,
        )
        campaign_results[kind] = result
        if result.get("verified") is not True:
            return {
                "verified": False,
                "bundle_sha256": actual_digest,
                "challenge": challenge,
                "campaigns": campaign_results,
                "problems": [f"CAMPAIGN_EVIDENCE_NOT_VERIFIED:{kind}"],
                "live_enabled": False,
                "production_ready": False,
            }

    shadow_metrics = campaign_results["live-shadow"].get("metrics", {})
    if shadow_metrics.get("real_orders_submitted") != 0 or shadow_metrics.get("exchange_submit_calls") != 0:
        return {
            "verified": False,
            "bundle_sha256": actual_digest,
            "challenge": challenge,
            "campaigns": campaign_results,
            "problems": ["LIVE_SHADOW_ORDER_SUBMISSION_DETECTED"],
            "live_enabled": False,
            "production_ready": False,
        }

    return {
        "schema_version": "1.0",
        "classification": "PHASE251_FINAL_CAMPAIGN_HANDOFF_VERIFICATION",
        "verified": True,
        "candidate_sha": candidate,
        "bundle_sha256": actual_digest,
        "acceptance_environment_id_sha256": environment_binding["acceptance_environment_id_hash"],
        "topology_hash": topology,
        "challenge": {
            "challenge_id": challenge.get("challenge_id"),
            "git_commit_sha": challenge.get("git_commit_sha"),
            "sha256": challenge.get("sha256"),
            "trust_verified": challenge.get("trust_verified"),
        },
        "campaigns": {
            kind: {"verified": result.get("verified"), "sha256": result.get("sha256")}
            for kind, result in campaign_results.items()
        },
        "live_enabled": False,
        "production_ready": False,
        "truth_policy": "This handoff only stages and verifies exact-SHA real campaign evidence. Live-shadow must prove zero real order submissions. It never enables LIVE trading.",
        "problems": [],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Fail-closed final campaign evidence handoff")
    parser.add_argument("--bundle", required=True)
    parser.add_argument("--expected-sha256", required=True)
    parser.add_argument("--expected-candidate", required=True)
    parser.add_argument("--expected-environment-id", required=True)
    parser.add_argument("--expected-topology-hash", required=True)
    parser.add_argument("--max-age-hours", type=int, default=168)
    parser.add_argument("--output", default=str(RECEIPT.relative_to(ROOT)))
    args = parser.parse_args()

    output = (ROOT / args.output).resolve()
    try:
        output.relative_to(ROOT.resolve())
    except ValueError:
        print(json.dumps({"verified": False, "problems": ["OUTPUT_PATH_OUTSIDE_ROOT"]}, sort_keys=True))
        return 2

    result = handoff(
        bundle=Path(args.bundle).expanduser().resolve(),
        expected_sha256=args.expected_sha256,
        expected_candidate=args.expected_candidate,
        expected_environment_id=args.expected_environment_id,
        expected_topology_hash=args.expected_topology_hash,
        max_age_hours=max(1, args.max_age_hours),
    )
    _write_receipt(result, output)
    print(json.dumps(result, sort_keys=True))
    return 0 if result.get("verified") is True else 2


if __name__ == "__main__":
    raise SystemExit(main())
