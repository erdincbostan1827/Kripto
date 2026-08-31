from __future__ import annotations

import json
import shutil
import socket
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class Check:
    key: str
    status: str
    detail: str


def _tool(name: str) -> Check:
    path = shutil.which(name)
    return Check(f"tool:{name}", "READY" if path else "BLOCKED", path or "NOT_INSTALLED")


def _dns(host: str) -> Check:
    try:
        rows = socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)
    except OSError as exc:
        return Check(f"dns:{host}", "BLOCKED", f"{type(exc).__name__}:{exc}")
    addresses = sorted({row[4][0] for row in rows if row[4]})
    return Check(f"dns:{host}", "READY", ",".join(addresses[:4]) or "RESOLVED")


def _file(rel: str) -> Check:
    path = ROOT / rel
    return Check(f"file:{rel}", "READY" if path.is_file() else "BLOCKED", "PRESENT" if path.is_file() else "MISSING")


def evaluate() -> dict:
    checks = [
        _tool("uv"),
        _tool("npm"),
        _file("pyproject.toml"),
        _file("frontend/package.json"),
        _file("uv.lock"),
        _file("frontend/package-lock.json"),
        _dns("pypi.org"),
        _dns("registry.npmjs.org"),
    ]
    by_key = {c.key: c for c in checks}
    manifests_ready = all(by_key[k].status == "READY" for k in ("file:pyproject.toml", "file:frontend/package.json"))
    tools_ready = all(by_key[k].status == "READY" for k in ("tool:uv", "tool:npm"))
    registries_resolvable = all(by_key[k].status == "READY" for k in ("dns:pypi.org", "dns:registry.npmjs.org"))
    locks_present = all(by_key[k].status == "READY" for k in ("file:uv.lock", "file:frontend/package-lock.json"))

    blockers: list[str] = []
    if not manifests_ready:
        blockers.append("DEPENDENCY_MANIFEST_MISSING")
    if not tools_ready:
        blockers.append("RESOLUTION_TOOLING_MISSING")
    if not registries_resolvable:
        blockers.append("REGISTRY_DNS_UNAVAILABLE")
    if not locks_present:
        blockers.append("SOURCE_LOCKS_MISSING")

    if locks_present:
        next_action = "VERIFY_COMMITTED_SOURCE_LOCKS"
    elif manifests_ready and tools_ready and registries_resolvable:
        next_action = "RUN_LOCK_PROMOTION_WORKFLOW_AND_REVIEW_COMMIT"
    elif not registries_resolvable:
        next_action = "RUN_LOCK_PROMOTION_IN_NETWORKED_TRUSTED_CI"
    else:
        next_action = "REPAIR_PREREQUISITES_BEFORE_LOCK_RESOLUTION"

    return {
        "schema_version": "1.0",
        "classification": "LOCAL_DEPENDENCY_RESOLUTION_DIAGNOSTIC_NOT_ACCEPTANCE_EVIDENCE",
        "checks": [asdict(c) for c in checks],
        "summary": {
            "manifests_ready": manifests_ready,
            "tools_ready": tools_ready,
            "registries_resolvable": registries_resolvable,
            "locks_present": locks_present,
            "blockers": blockers,
            "next_action": next_action,
        },
        "truth_policy": "DNS/tool presence is prerequisite evidence only. It does not prove dependency integrity, vulnerability status, license acceptance, or production readiness.",
    }


def main() -> int:
    payload = evaluate()
    out = ROOT / "reports" / "DEPENDENCY_RESOLUTION_DIAGNOSTIC.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload["summary"]["locks_present"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
