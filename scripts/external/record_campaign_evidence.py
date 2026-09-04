from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.release.acceptance_challenge import verify_challenge
from backend.app.release.campaign_acceptance import verify_campaign_evidence
from backend.app.release.campaign_evidence_recorder import (
    EVENT_KINDS,
    append_event,
    derive_metrics,
    initialize_journal,
    load_journal,
    write_receipts,
)

DEFAULT_JOURNAL = ROOT / "reports/external_acceptance/campaign/source/phase263_campaign.jsonl"
DEFAULT_OUTPUT = ROOT / "reports/external_acceptance/campaign"


def _exact_sha(value: str) -> str:
    candidate = value.strip().lower()
    if len(candidate) != 40 or any(c not in "0123456789abcdef" for c in candidate):
        raise ValueError("git HEAD must resolve to an exact 40-char commit SHA")
    return candidate


def _git_sha() -> str:
    git_dir = ROOT / ".git"
    if not git_dir.is_dir():
        raise RuntimeError("acceptance recording requires a regular Git checkout with a .git directory")
    head = (git_dir / "HEAD").read_text(encoding="utf-8").strip()
    if not head.startswith("ref: "):
        return _exact_sha(head)
    ref = head[5:].strip()
    if not ref.startswith("refs/") or ".." in ref.split("/"):
        raise ValueError("git HEAD contains an unsafe ref")
    loose = git_dir / Path(*ref.split("/"))
    if loose.is_file():
        return _exact_sha(loose.read_text(encoding="utf-8").strip())
    packed = git_dir / "packed-refs"
    if packed.is_file():
        for line in packed.read_text(encoding="utf-8").splitlines():
            if not line or line.startswith(("#", "^")):
                continue
            parts = line.split(" ", 1)
            if len(parts) == 2 and parts[1].strip() == ref:
                return _exact_sha(parts[0])
    raise RuntimeError("git HEAD ref could not be resolved without invoking an external process")


def _inside_root(path: Path) -> Path:
    resolved = path.resolve()
    resolved.relative_to(ROOT.resolve())
    return resolved


def _environment() -> tuple[str, str, str]:
    environment_id = os.getenv("ACCEPTANCE_ENVIRONMENT_ID", "").strip()
    topology = os.getenv("ACCEPTANCE_TOPOLOGY_HASH", "").strip().lower()
    if not environment_id:
        raise ValueError("ACCEPTANCE_ENVIRONMENT_ID is required")
    if len(topology) != 64 or any(c not in "0123456789abcdef" for c in topology):
        raise ValueError("ACCEPTANCE_TOPOLOGY_HASH must be exact 64-char lowercase hex")
    environment_hash = hashlib.sha256(environment_id.encode()).hexdigest()
    return environment_id, environment_hash, topology


def _verified_challenge(candidate: str) -> dict[str, Any]:
    path = ROOT / "reports/external_acceptance/release_challenge.json"
    result = verify_challenge(path, root=ROOT, require_trust=True)
    if result.get("verified") is not True or result.get("trust_verified") is not True:
        raise PermissionError("release challenge is not externally trust-verified")
    bound_commit = str(result.get("git_commit_sha") or result.get("candidate_sha") or "").lower()
    if bound_commit and bound_commit != candidate:
        raise PermissionError("release challenge is bound to a different candidate SHA")
    challenge_id = str(result.get("challenge_id") or "").strip()
    challenge_sha = str(result.get("sha256") or "").strip().lower()
    if not challenge_id or len(challenge_sha) != 64:
        raise PermissionError("release challenge identity is incomplete")
    return result


def _load_payload(path: Path) -> dict[str, Any]:
    loaded = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        raise ValueError("event payload must be a JSON object")
    return loaded


def _cmd_init(args: argparse.Namespace) -> int:
    journal = _inside_root(Path(args.journal))
    candidate = _git_sha()
    challenge = _verified_challenge(candidate)
    _, environment_hash, topology = _environment()
    record = initialize_journal(
        journal,
        candidate_sha=candidate,
        challenge_id=str(challenge["challenge_id"]),
        challenge_sha256=str(challenge["sha256"]),
        acceptance_environment_id_hash=environment_hash,
        topology_hash=topology,
    )
    print(json.dumps({"initialized": True, "journal": journal.relative_to(ROOT).as_posix(), "header": record}, sort_keys=True))
    return 0


def _cmd_append(args: argparse.Namespace) -> int:
    journal = _inside_root(Path(args.journal))
    payload_path = Path(args.payload_file).resolve()
    record = append_event(journal, kind=args.kind, payload=_load_payload(payload_path))
    print(json.dumps({"appended": True, "sequence": record["sequence"], "kind": record["kind"]}, sort_keys=True))
    return 0


def _cmd_status(args: argparse.Namespace) -> int:
    journal = _inside_root(Path(args.journal))
    rows = load_journal(journal)
    print(json.dumps({"records": len(rows), "metrics": derive_metrics(rows)}, indent=2, sort_keys=True))
    return 0


def _cmd_finalize(args: argparse.Namespace) -> int:
    journal = _inside_root(Path(args.journal))
    output = _inside_root(Path(args.output_dir))
    candidate = _git_sha()
    rows = load_journal(journal)
    if rows[0].get("candidate_sha") != candidate:
        raise PermissionError("campaign journal candidate SHA does not match current git HEAD")
    _verified_challenge(candidate)
    _, environment_hash, topology = _environment()
    if rows[0].get("acceptance_environment_id_hash") != environment_hash or rows[0].get("topology_hash") != topology:
        raise PermissionError("campaign journal environment/topology binding does not match current acceptance target")
    written = write_receipts(journal, root=ROOT, output_dir=output)
    expected_environment = {
        "acceptance_environment_id_hash": environment_hash,
        "topology_hash": topology,
    }
    results: dict[str, Any] = {}
    for kind, path in written.items():
        results[kind] = verify_campaign_evidence(
            path,
            kind=kind,
            root=ROOT,
            strict_external=True,
            expected_environment=expected_environment,
        )
    selected_all_pass = all(row.get("verified") is True for row in results.values())
    print(
        json.dumps(
            {
                "classification": "PHASE263_CAMPAIGN_RECORDING_STATUS",
                "candidate_sha": candidate,
                "selected_all_pass": selected_all_pass,
                "live_enabled": False,
                "production_ready": False,
                "groups": results,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if selected_all_pass else 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Record tamper-evident real campaign observations and derive Phase246-compatible receipts."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    init = sub.add_parser("init")
    init.add_argument("--journal", default=str(DEFAULT_JOURNAL))
    init.set_defaults(func=_cmd_init)

    append = sub.add_parser("append")
    append.add_argument("--journal", default=str(DEFAULT_JOURNAL))
    append.add_argument("--kind", required=True, choices=sorted(EVENT_KINDS))
    append.add_argument("--payload-file", required=True)
    append.set_defaults(func=_cmd_append)

    status = sub.add_parser("status")
    status.add_argument("--journal", default=str(DEFAULT_JOURNAL))
    status.set_defaults(func=_cmd_status)

    finalize = sub.add_parser("finalize")
    finalize.add_argument("--journal", default=str(DEFAULT_JOURNAL))
    finalize.add_argument("--output-dir", default=str(DEFAULT_OUTPUT))
    finalize.set_defaults(func=_cmd_finalize)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        return int(args.func(args))
    except Exception as exc:
        print(json.dumps({"error": type(exc).__name__, "message": str(exc), "production_ready": False, "live_enabled": False}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
