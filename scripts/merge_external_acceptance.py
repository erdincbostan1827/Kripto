from __future__ import annotations

import argparse
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
GIT_PROBE_TIMEOUT_SECONDS = 10

from backend.app.release.acceptance_challenge import verify_challenge
from backend.app.release.evidence_ledger import append_entry
from backend.app.release.acceptance_contract import PROFILE_TO_GROUPS
from scripts.verify_external_acceptance import GROUP_KEYS, verify_manifest
from scripts.external_acceptance_runner import command_contract_sha256
from scripts.bounded_subprocess import run_captured_split


def _sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _git_sha(root: Path) -> str:
    try:
        proc = run_captured_split(["git", "rev-parse", "HEAD"], cwd=root, timeout=GIT_PROBE_TIMEOUT_SECONDS)
    except (subprocess.TimeoutExpired, OSError):
        return "UNAVAILABLE"
    value = (proc.stdout or "").strip()
    return value if proc.returncode == 0 and value else "UNAVAILABLE"


def merge(*, root: Path = ROOT, max_age_hours: int = 168) -> dict[str, Any]:
    reports = root / "reports" / "external_acceptance"
    challenge = verify_challenge(reports / "release_challenge.json", root=root)
    git_sha = _git_sha(root)
    groups = {name: "NOT_TESTED" for name in GROUP_KEYS}
    evidence: list[dict[str, Any]] = []
    sources: dict[str, Any] = {}
    problems: list[str] = []
    if git_sha == "UNAVAILABLE":
        problems.append("GIT_IDENTITY_UNAVAILABLE")
    environment_identities: set[tuple[str, str]] = set()

    for profile, profile_groups in PROFILE_TO_GROUPS.items():
        path = reports / f"manifest_{profile}.json"
        if not path.is_file():
            sources[profile] = {"status": "MISSING", "reference": None}
            continue
        result = verify_manifest(path, root=root, max_age_hours=max_age_hours)
        sources[profile] = {
            "status": "VERIFIED" if result.get("verified") else "INVALID",
            "reference": str(path.relative_to(root)),
            "sha256": result.get("manifest_sha256"),
            "problems": result.get("problems", []),
        }
        if not result.get("verified"):
            problems.extend(f"PROFILE_INVALID:{profile}:{p}" for p in result.get("problems", []))
            for actual_group in profile_groups:
                groups[actual_group] = "BLOCKED"
            continue
        doc = json.loads(path.read_text(encoding="utf-8"))
        env = doc.get("environment") if isinstance(doc.get("environment"), dict) else {}
        env_id = env.get("acceptance_environment_id_hash")
        topology = env.get("topology_hash")
        if any(result.get("groups", {}).get(g) == "PASS" for g in profile_groups):
            if not isinstance(env_id, str) or not isinstance(topology, str):
                problems.append(f"PROFILE_ENVIRONMENT_IDENTITY_MISSING:{profile}")
            else:
                environment_identities.add((env_id, topology))
        rows = {r.get("key"): r for r in doc.get("evidence", []) if isinstance(r, dict)}
        for actual_group in profile_groups:
            groups[actual_group] = result.get("groups", {}).get(actual_group, "NOT_TESTED")
            for key in GROUP_KEYS[actual_group]:
                row = rows.get(key)
                if row is not None:
                    evidence.append(row)

    any_real_source = any(v.get("status") == "VERIFIED" for v in sources.values())
    any_pass_group = any(v == "PASS" for v in groups.values())
    # Aggregate PASS is release-relevant. Re-verify the current challenge with
    # external trust *before* claiming a real target or appending to the ledger.
    # Individual profile verification already enforces this, but the merger must
    # independently fail closed so a mutated/intermediate profile set cannot
    # create aggregate release metadata under an untrusted challenge.
    if any_pass_group:
        challenge = verify_challenge(reports / "release_challenge.json", root=root, require_trust=True)
        if not challenge.get("verified"):
            problems.append("MERGE_RELEASE_CHALLENGE_NOT_TRUSTED")
            for group, status in list(groups.items()):
                if status == "PASS":
                    groups[group] = "BLOCKED"
            any_pass_group = False
    if len(environment_identities) > 1:
        problems.append("CROSS_PROFILE_ENVIRONMENT_IDENTITY_MISMATCH")
        for group, status in list(groups.items()):
            if status == "PASS":
                groups[group] = "BLOCKED"
    merged_env_id = merged_topology = None
    if len(environment_identities) == 1:
        merged_env_id, merged_topology = next(iter(environment_identities))
    payload = {
        "schema_version": "4.1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "classification": "EXTERNAL_ACCEPTANCE_EVIDENCE_BUNDLE",
        "truth_policy": "Merged PASS is allowed only from individually verified, release-bound profile manifests. Missing or invalid profiles remain NOT_TESTED/BLOCKED.",
        "profile": "all",
        "command_contract_sha256": command_contract_sha256("all"),
        "real_target_explicitly_confirmed": bool(any_real_source and any_pass_group and challenge.get("verified") and challenge.get("trust_verified")),
        "challenge": challenge,
        "environment": {"git_commit_sha": git_sha, "acceptance_environment_id_hash": merged_env_id, "topology_hash": merged_topology},
        "credentials": {"binance_testnet": "REDACTED_OR_NOT_EVALUATED"},
        "evidence": evidence,
        "groups": groups,
        "selected_all_pass": git_sha != "UNAVAILABLE" and not problems and all(v == "PASS" for v in groups.values()),
        "source_profiles": sources,
        "merge_problems": problems,
    }
    out = reports / "manifest_all.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    manifest_sha = _sha(out)

    # Any PASS group makes the aggregate release-relevant. Bind the aggregate itself
    # into the append-only ledger so verify_manifest can detect replacement/replay.
    if git_sha != "UNAVAILABLE" and not problems and any(v == "PASS" for v in groups.values()) and challenge.get("verified") and challenge.get("trust_verified"):
        append_entry(
            reports / "evidence_ledger.json",
            manifest_sha256=manifest_sha,
            challenge_id=str(challenge.get("challenge_id")),
            git_commit_sha=git_sha,
            profile="all-merged",
            root=root,
        )

    verification = verify_manifest(out, root=root, max_age_hours=max_age_hours)
    return {
        "manifest": str(out.relative_to(root)),
        "manifest_sha256": manifest_sha,
        "groups": groups,
        "selected_all_pass": payload["selected_all_pass"],
        "source_profiles": sources,
        "merge_problems": problems,
        "verification": verification,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Merge release-bound external acceptance profile manifests into manifest_all.json")
    parser.add_argument("--max-age-hours", type=int, default=168)
    args = parser.parse_args()
    result = merge(max_age_hours=max(1, args.max_age_hours))
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["verification"].get("verified") and result["selected_all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
