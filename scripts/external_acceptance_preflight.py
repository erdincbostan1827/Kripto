from __future__ import annotations

import json
import os
import shutil
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.verify_source_locks import verify_source_locks

@dataclass(frozen=True)
class Check:
    key: str
    status: str
    detail: str
    evidence: str | None = None


def _hash(path: Path) -> str | None:
    if not path.is_file():
        return None
    return sha256(path.read_bytes()).hexdigest()


def _tool(name: str) -> Check:
    path = shutil.which(name)
    return Check(f"tool:{name}", "READY" if path else "BLOCKED", path or f"TOOL_UNAVAILABLE:{name}")


def _source_lock_checks() -> list[Check]:
    result = verify_source_locks(ROOT)
    rows = {row["path"]: row for row in result["locks"]}
    checks: list[Check] = []
    for rel in ("uv.lock", "frontend/package-lock.json"):
        row = rows[rel]
        if row["source_compliant"]:
            checks.append(Check(
                f"file:{rel}", "READY",
                f"tracked_in_head=true matches_head=true sha256={row['working_tree_sha256']}", rel,
            ))
        else:
            reason = next((p.split(":", 1)[1] for p in result["problems"] if p.startswith(rel + ":")), "NON_COMPLIANT")
            checks.append(Check(
                f"file:{rel}", "BLOCKED",
                f"SOURCE_LOCK_NON_COMPLIANT:{reason}", None,
            ))
    return checks


def _env(name: str) -> Check:
    present = bool(os.getenv(name))
    # Never expose credential values.
    return Check(f"env:{name}", "READY" if present else "BLOCKED", "PRESENT_REDACTED" if present else "MISSING")


def evaluate() -> dict:
    checks = [
        _tool("docker"), _tool("uv"), _tool("npm"),
        *_source_lock_checks(),
        _env("BINANCE_TESTNET_API_KEY"), _env("BINANCE_TESTNET_API_SECRET"),
        _env("PITR_DRILL_COMMAND"), _env("PITR_EVIDENCE_JSON"),
        _env("HA_DRILL_COMMAND"), _env("HA_EVIDENCE_JSON"),
        _env("WORM_ACCEPTANCE_COMMAND"), _env("WORM_EVIDENCE_JSON"),
        _env("ACCEPTANCE_ENVIRONMENT_ID"), _env("ACCEPTANCE_TOPOLOGY_HASH"),
        _env("ACCEPTANCE_CHALLENGE_VERIFY_COMMAND"), _env("PROVENANCE_SIGN_VERIFY_COMMAND"),
        _env("LEDGER_CHECKPOINT_SIGN_COMMAND"), _env("ACCEPTANCE_LEDGER_CHECKPOINT_VERIFY_COMMAND"),
        _env("RESTART_DRILL_COMMAND"), _env("RESTART_EVIDENCE_JSON"),
    ]
    groups = {
        "dependency_locks": all(c.status == "READY" for c in checks if c.key in {"file:uv.lock", "file:frontend/package-lock.json"}),
        "container_runtime": next(c for c in checks if c.key == "tool:docker").status == "READY",
        "credentialed_testnet": all(c.status == "READY" for c in checks if c.key.startswith("env:BINANCE_TESTNET_")),
        "transferred_supply_chain_contract": True,
        "pitr_contract": all(next(c for c in checks if c.key == f"env:{n}").status == "READY" for n in ("PITR_DRILL_COMMAND","PITR_EVIDENCE_JSON")),
        "ha_contract": all(next(c for c in checks if c.key == f"env:{n}").status == "READY" for n in ("HA_DRILL_COMMAND","HA_EVIDENCE_JSON")),
        "worm_contract": all(next(c for c in checks if c.key == f"env:{n}").status == "READY" for n in ("WORM_ACCEPTANCE_COMMAND","WORM_EVIDENCE_JSON")),
        "restart_contract": all(next(c for c in checks if c.key == f"env:{n}").status == "READY" for n in ("RESTART_DRILL_COMMAND","RESTART_EVIDENCE_JSON")),
        "signing_tooling": next(c for c in checks if c.key == "env:PROVENANCE_SIGN_VERIFY_COMMAND").status == "READY",
        "environment_identity": all(next(c for c in checks if c.key == f"env:{n}").status == "READY" for n in ("ACCEPTANCE_ENVIRONMENT_ID","ACCEPTANCE_TOPOLOGY_HASH")),
        "challenge_trust_contract": next(c for c in checks if c.key == "env:ACCEPTANCE_CHALLENGE_VERIFY_COMMAND").status == "READY",
        "provenance_sign_verify_contract": next(c for c in checks if c.key == "env:PROVENANCE_SIGN_VERIFY_COMMAND").status == "READY",
        "ledger_checkpoint_contract": all(next(c for c in checks if c.key == f"env:{n}").status == "READY" for n in ("LEDGER_CHECKPOINT_SIGN_COMMAND","ACCEPTANCE_LEDGER_CHECKPOINT_VERIFY_COMMAND")),
    }
    return {
        "schema_version": "1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "classification": "EXTERNAL_ACCEPTANCE_PREFLIGHT_ONLY_NOT_ACCEPTANCE_EVIDENCE",
        "truth_policy": "READY means prerequisite detected only; it never means the corresponding external acceptance test passed.",
        "checks": [asdict(c) for c in checks],
        "groups": groups,
        "all_external_prerequisites_ready": all(groups.values()),
    }


def main() -> int:
    payload = evaluate()
    out = ROOT / "reports" / "EXTERNAL_ACCEPTANCE_PREFLIGHT.json"
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload["all_external_prerequisites_ready"] else 2

if __name__ == "__main__":
    raise SystemExit(main())
