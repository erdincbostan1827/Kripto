from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import sys
import subprocess

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.external.execution_map import build as build_execution_map
from scripts.external.frontend_browser_acceptance import run as run_frontend_browser
from scripts.external.tauri_build_readiness import evaluate as evaluate_tauri_build
from scripts.production_acceptance_orchestrator import orchestrate

OUT = ROOT / "reports" / "EXTERNAL_REQUIREMENTS_MASTER_EXECUTION.json"


def _profile_counts(execution_map: dict[str, Any]) -> dict[str, int]:
    return {str(k): int(v) for k, v in execution_map.get("profiles", {}).items()}


def _write(payload: dict[str, Any]) -> dict[str, Any]:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def _current_git_sha() -> str | None:
    try:
        p = subprocess.run(['git','rev-parse','HEAD'], cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=10, check=False)
        value = (p.stdout or '').strip().lower()
        return value if p.returncode == 0 and len(value) == 40 else None
    except Exception:
        return None


def _source_binding(*, canonical: dict[str, Any], frontend: dict[str, Any], tauri: dict[str, Any]) -> dict[str, Any]:
    expected = _current_git_sha()
    observed = {
        'current_git_sha': expected,
        'canonical_challenge_git_sha': (canonical.get('challenge') or {}).get('git_commit_sha'),
        'canonical_verified_challenge_git_sha': (canonical.get('challenge_verification') or {}).get('git_commit_sha'),
        'frontend_git_sha': frontend.get('git_commit_sha'),
        'tauri_git_sha': tauri.get('git_commit_sha'),
    }
    problems: list[str] = []
    if expected is None:
        problems.append('CURRENT_GIT_IDENTITY_UNAVAILABLE')
    else:
        for name, value in observed.items():
            if name == 'current_git_sha':
                continue
            if value != expected:
                problems.append(f'SOURCE_IDENTITY_MISMATCH:{name}')
    f_lock = frontend.get('frontend_lock_sha256')
    t_lock = tauri.get('frontend_lock_sha256')
    if f_lock is None or t_lock is None:
        problems.append('FRONTEND_LOCK_IDENTITY_MISSING')
    elif f_lock != t_lock:
        problems.append('FRONTEND_LOCK_IDENTITY_MISMATCH')
    return {
        'verified': not problems,
        'expected_git_sha': expected,
        'observed': observed,
        'frontend_lock_sha256': f_lock,
        'tauri_frontend_lock_sha256': t_lock,
        'problems': sorted(set(problems)),
    }


def execute_all(*, confirm_real: bool, timeout: int = 600) -> dict[str, Any]:
    execution_map = build_execution_map()
    base = {
        "schema_version": "1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "classification": "EXTERNAL_REQUIREMENTS_MASTER_EXECUTION_NOT_SELF_ACCEPTANCE_EVIDENCE",
        "truth_policy": (
            "This coordinator can schedule every currently unresolved external requirement, but it cannot by itself "
            "promote a requirement to PASS. Canonical profiles require challenge-bound external evidence; frontend/browser "
            "and desktop build require their own real-target evidence. production_ready remains false unless the canonical "
            "release gate and every standalone required step pass on the same source state."
        ),
        "open_requirement_count": execution_map["open_requirement_count"],
        "mapped_requirement_count": execution_map["mapped_requirement_count"],
        "unmapped_requirement_count": execution_map["unmapped_requirement_count"],
        "profile_requirement_counts": _profile_counts(execution_map),
        "real_target_explicitly_confirmed": bool(confirm_real),
    }
    if not confirm_real:
        return _write({
            **base,
            "executed": False,
            "production_ready": False,
            "all_required_execution_steps_pass": False,
            "blockers": ["REAL_TARGET_NOT_EXPLICITLY_CONFIRMED"],
            "planned_commands": sorted({row["command"] for row in execution_map["requirements"]}),
        })

    # Canonical acceptance owns challenge creation, immutable profile manifests,
    # external merge/verification and the production release gate.
    canonical = orchestrate(confirm_real=True, timeout=timeout)
    frontend = run_frontend_browser(timeout=timeout, confirm_real=True)
    tauri = evaluate_tauri_build(confirm_real=True, timeout=timeout)

    standalone = {
        "frontend-browser": {
            "verified": bool(frontend.get("verified")),
            "git_commit_sha": frontend.get("git_commit_sha"),
            "manifest_sha256": frontend.get("manifest_sha256"),
            "frontend_lock_sha256": frontend.get("frontend_lock_sha256"),
            "blockers": frontend.get("blockers", []),
        },
        "desktop-build": {
            "verified": bool(tauri.get("verified")),
            "git_commit_sha": tauri.get("git_commit_sha"),
            "manifest_sha256": tauri.get("manifest_sha256"),
            "frontend_lock_sha256": tauri.get("frontend_lock_sha256"),
            "cargo_lock_sha256": tauri.get("cargo_lock_sha256"),
            "blockers": tauri.get("blockers", []),
        },
    }
    canonical_profiles_pass = all(
        bool(v.get("selected_all_pass")) for v in canonical.get("profiles", {}).values()
    ) and bool(canonical.get("profiles"))
    standalone_pass = all(v["verified"] for v in standalone.values())
    source_binding = _source_binding(canonical=canonical, frontend=frontend, tauri=tauri)
    all_steps = bool(canonical_profiles_pass and standalone_pass and source_binding["verified"])
    production_ready = bool(canonical.get("production_ready") and all_steps)

    blockers: list[str] = []
    if not canonical_profiles_pass:
        blockers.append("CANONICAL_EXTERNAL_PROFILES_NOT_ALL_PASS")
    if not standalone["frontend-browser"]["verified"]:
        blockers.append("FRONTEND_BROWSER_ACCEPTANCE_NOT_PASS")
    if not standalone["desktop-build"]["verified"]:
        blockers.append("DESKTOP_BUILD_READINESS_NOT_PASS")
    if not source_binding["verified"]:
        blockers.append("SOURCE_IDENTITY_BINDING_NOT_PASS")
    if not canonical.get("production_ready"):
        blockers.append("CANONICAL_RELEASE_GATE_NOT_PASS")

    return _write({
        **base,
        "executed": True,
        "canonical": canonical,
        "standalone": standalone,
        "source_identity_binding": source_binding,
        "canonical_profiles_pass": canonical_profiles_pass,
        "standalone_required_steps_pass": standalone_pass,
        "all_required_execution_steps_pass": all_steps,
        "production_ready": production_ready,
        "blockers": sorted(set(blockers)),
    })


def main() -> int:
    ap = argparse.ArgumentParser(description="Fail-closed master coordinator for all unresolved external requirements")
    ap.add_argument("--confirm-real-target", action="store_true")
    ap.add_argument("--timeout", type=int, default=600)
    args = ap.parse_args()
    result = execute_all(confirm_real=args.confirm_real_target, timeout=max(1, args.timeout))
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get("production_ready") is True else 2


if __name__ == "__main__":
    raise SystemExit(main())
