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
from backend.app.release.campaign_evidence_recorder import derive_metrics, initialize_journal, load_journal

DEFAULT_JOURNAL = ROOT / "reports/external_acceptance/campaign/source/phase263_campaign.jsonl"
LEGACY_BLOCKER = (
    "Phase263 legacy recorder is audit-only. Arbitrary append/finalize is disabled; "
    "use Phase265 protected-runtime HMAC-attested telemetry and fresh-challenge sealing."
)


def _exact_sha(value: str) -> str:
    candidate = value.strip().lower()
    if len(candidate) != 40 or any(c not in "0123456789abcdef" for c in candidate):
        raise ValueError("git HEAD must resolve to an exact 40-char commit SHA")
    return candidate


def _git_sha() -> str:
    git_dir = ROOT / ".git"
    if not git_dir.is_dir():
        raise RuntimeError("campaign audit requires a regular Git checkout with a .git directory")
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
    print(
        json.dumps(
            {
                "classification": "PHASE263_LEGACY_JOURNAL_AUDIT_NOT_ACCEPTANCE_EVIDENCE",
                "initialized": True,
                "journal": journal.relative_to(ROOT).as_posix(),
                "header": record,
                "blocker": LEGACY_BLOCKER,
                "production_ready": False,
                "live_enabled": False,
            },
            sort_keys=True,
        )
    )
    return 0


def _cmd_append(args: argparse.Namespace) -> int:
    del args
    raise PermissionError(LEGACY_BLOCKER)


def _cmd_status(args: argparse.Namespace) -> int:
    journal = _inside_root(Path(args.journal))
    rows = load_journal(journal)
    print(
        json.dumps(
            {
                "classification": "PHASE263_LEGACY_JOURNAL_AUDIT_NOT_ACCEPTANCE_EVIDENCE",
                "records": len(rows),
                "metrics": derive_metrics(rows),
                "blocker": LEGACY_BLOCKER,
                "production_ready": False,
                "live_enabled": False,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


def _cmd_finalize(args: argparse.Namespace) -> int:
    del args
    raise PermissionError(LEGACY_BLOCKER)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Legacy Phase263 campaign journal inspection. Acceptance mutation/finalization is disabled."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    init = sub.add_parser("init", help="Create a challenge-bound legacy audit journal; not acceptance evidence")
    init.add_argument("--journal", default=str(DEFAULT_JOURNAL))
    init.set_defaults(func=_cmd_init)

    append = sub.add_parser("append", help="Disabled: arbitrary event append cannot create acceptance evidence")
    append.add_argument("--journal", default=str(DEFAULT_JOURNAL))
    append.add_argument("--kind", required=True)
    append.add_argument("--payload-file", required=True)
    append.set_defaults(func=_cmd_append)

    status = sub.add_parser("status", help="Inspect a legacy journal without claiming acceptance")
    status.add_argument("--journal", default=str(DEFAULT_JOURNAL))
    status.set_defaults(func=_cmd_status)

    finalize = sub.add_parser("finalize", help="Disabled: use Phase265 protected-runtime attested sealing")
    finalize.add_argument("--journal", default=str(DEFAULT_JOURNAL))
    finalize.add_argument("--output-dir", default=str(ROOT / "reports/external_acceptance/campaign"))
    finalize.set_defaults(func=_cmd_finalize)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        return int(args.func(args))
    except Exception as exc:
        print(
            json.dumps(
                {
                    "error": type(exc).__name__,
                    "message": str(exc),
                    "production_ready": False,
                    "live_enabled": False,
                }
            )
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
