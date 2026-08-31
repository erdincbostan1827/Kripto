from __future__ import annotations

import json
import shutil
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "reports" / "external_acceptance" / "toolchain_readiness.json"


@dataclass(frozen=True)
class Tool:
    name: str
    status: str
    path: str | None


def _tool(name: str) -> Tool:
    path = shutil.which(name)
    return Tool(name, "READY" if path else "BLOCKED", path)


def evaluate() -> dict:
    names = (
        "docker", "uv", "npm", "chromium", "cargo", "rustc",
        "pip-audit", "bandit", "semgrep", "trivy", "gitleaks", "syft",
        "pip-licenses", "cosign",
    )
    rows = [_tool(name) for name in names]
    by = {row.name: row for row in rows}
    groups = {
        "container_runtime": by["docker"].status == "READY",
        "frontend_browser_tooling": all(by[n].status == "READY" for n in ("npm", "chromium")),
        "desktop_build_tooling": all(by[n].status == "READY" for n in ("npm", "cargo", "rustc")),
        "supply_chain_scanner_tooling": all(by[n].status == "READY" for n in ("pip-audit", "bandit", "semgrep", "trivy", "gitleaks", "syft", "pip-licenses")),
        "artifact_signing_tooling": by["cosign"].status == "READY",
    }
    return {
        "schema_version": "1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "classification": "STANDALONE_TOOLCHAIN_READINESS_NOT_ACCEPTANCE_EVIDENCE",
        "truth_policy": "Tool presence is readiness information only. It is not canonical external acceptance and cannot promote any requirement or release gate to PASS.",
        "tools": [asdict(row) for row in rows],
        "groups": groups,
        "all_groups_ready": all(groups.values()),
    }


def main() -> int:
    payload = evaluate()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload["all_groups_ready"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
