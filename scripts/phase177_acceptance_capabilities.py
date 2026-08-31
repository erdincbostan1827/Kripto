from __future__ import annotations

import importlib.util
import json
import shutil
import socket
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.acceptance_closure_status import build as build_closure
from scripts.external_acceptance_preflight import evaluate as evaluate_preflight

OUT = ROOT / "reports" / "PHASE177_ACCEPTANCE_CAPABILITIES.json"

TOOLS = ("git", "python", "uv", "npm", "node", "docker", "podman", "cargo", "rustc", "trivy", "gitleaks", "bandit", "semgrep", "pip-audit", "syft", "cosign", "chromium", "google-chrome", "firefox")


def _dns(host: str) -> dict:
    try:
        socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)
        return {"host": host, "status": "READY", "detail": "DNS_RESOLVED"}
    except OSError as exc:
        return {"host": host, "status": "BLOCKED", "detail": f"DNS_UNAVAILABLE:{type(exc).__name__}"}


def build(*, probe_dns: bool = True) -> dict:
    closure = build_closure()
    preflight = evaluate_preflight()
    tools = [{"name": name, "status": "READY" if shutil.which(name) else "BLOCKED", "path": shutil.which(name)} for name in TOOLS]
    python_playwright = importlib.util.find_spec("playwright") is not None
    browser_engine = any(shutil.which(name) for name in ("chromium", "google-chrome", "firefox"))
    frontend_lock_ready = bool(preflight["groups"].get("dependency_locks"))
    profiles = {
        "frontend-browser": {
            "host_tooling_ready": bool(python_playwright and browser_engine),
            "dependency_locks_ready": frontend_lock_ready,
            "runnable_now": bool(python_playwright and browser_engine and frontend_lock_ready),
            "detail": "Browser engine and Playwright are host capabilities only; frontend dependency locks/build remain mandatory.",
        },
        "runtime": {
            "host_tooling_ready": bool(shutil.which("docker") or shutil.which("podman")),
            "runnable_now": bool(preflight["groups"].get("container_runtime")),
        },
        "supply-chain": {
            "available_scanners": [name for name in ("trivy", "gitleaks", "bandit", "semgrep", "pip-audit", "syft", "cosign") if shutil.which(name)],
            "trusted_ci_still_required": True,
            "runnable_now": False,
        },
        "dependency-locks": {
            "uv_available": bool(shutil.which("uv")),
            "npm_available": bool(shutil.which("npm")),
            "source_locks_ready": frontend_lock_ready,
            "runnable_now": bool(shutil.which("uv") and shutil.which("npm")),
            "acceptance_complete": frontend_lock_ready,
        },
    }
    return {
        "schema_version": "1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "classification": "PHASE177_HOST_CAPABILITY_DIAGNOSTIC_NOT_ACCEPTANCE_EVIDENCE",
        "truth_policy": "Host capabilities and successful DNS/tool probes are prerequisites only; they never promote requirements or release gates to PASS.",
        "open_requirement_count": closure["open_requirement_count"],
        "p0_open_requirement_count": closure["p0_open_requirement_count"],
        "tools": tools,
        "python_modules": {"playwright": "READY" if python_playwright else "BLOCKED"},
        "network_dns": [_dns("pypi.org"), _dns("registry.npmjs.org")] if probe_dns else [],
        "profiles": profiles,
    }


def main() -> int:
    payload = build()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
