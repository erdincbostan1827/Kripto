from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Mapping, Sequence

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.bounded_subprocess import run_captured_split
from scripts.verify_source_locks import verify_source_locks

DEFAULT_OUTPUT = ROOT / "reports" / "production_acceptance" / "PRODUCTION_RUNNER_READINESS.json"
REQUIRED_TOOLS = ("git", "bash", "docker")


def _probe(command: Sequence[str], *, root: Path, timeout: float = 20) -> tuple[bool, str]:
    try:
        proc = run_captured_split(command, cwd=root, timeout=timeout)
    except Exception as exc:
        return False, f"probe_error:{type(exc).__name__}"
    output = ((proc.stdout or "") + "\n" + (proc.stderr or "")).strip()
    first_line = output.splitlines()[0][:240] if output else ""
    return proc.returncode == 0, first_line or f"exit_code:{proc.returncode}"


def run_readiness(
    root: Path = ROOT,
    *,
    env: Mapping[str, str] | None = None,
    which: Callable[[str], str | None] = shutil.which,
    probe: Callable[..., tuple[bool, str]] = _probe,
    require_actions_context: bool = False,
) -> dict[str, object]:
    environment = dict(os.environ if env is None else env)
    checks: dict[str, dict[str, object]] = {}
    problems: list[str] = []

    def record(check_id: str, ok: bool, detail: str) -> None:
        checks[check_id] = {"ok": bool(ok), "detail": detail}
        if not ok:
            problems.append(check_id)

    for tool in REQUIRED_TOOLS:
        path = which(tool)
        record(f"TOOL_AVAILABLE:{tool}", path is not None, "available" if path else "missing")

    action_markers = {
        "GITHUB_ACTIONS": environment.get("GITHUB_ACTIONS", ""),
        "RUNNER_NAME": environment.get("RUNNER_NAME", ""),
        "RUNNER_OS": environment.get("RUNNER_OS", ""),
        "RUNNER_ARCH": environment.get("RUNNER_ARCH", ""),
    }
    if require_actions_context:
        record("GITHUB_ACTIONS_CONTEXT", action_markers["GITHUB_ACTIONS"].lower() == "true", "present" if action_markers["GITHUB_ACTIONS"].lower() == "true" else "missing")
        for name in ("RUNNER_NAME", "RUNNER_OS", "RUNNER_ARCH"):
            record(f"RUNNER_CONTEXT:{name}", bool(action_markers[name].strip()), "present" if action_markers[name].strip() else "missing")

    commands = (
        ("GIT_COMMAND", ("git", "--version")),
        ("BASH_COMMAND", ("bash", "--version")),
        ("DOCKER_DAEMON", ("docker", "info", "--format", "{{.ServerVersion}}")),
        ("DOCKER_COMPOSE", ("docker", "compose", "version", "--short")),
        ("DOCKER_COMPOSE_CONFIG", ("docker", "compose", "config", "--quiet")),
        ("GIT_HEAD", ("git", "rev-parse", "HEAD")),
    )
    for check_id, command in commands:
        if which(command[0]) is None:
            record(check_id, False, f"tool_missing:{command[0]}")
            continue
        ok, detail = probe(command, root=root)
        record(check_id, ok, detail)

    source_locks = verify_source_locks(root)
    record("SOURCE_LOCKS_VERIFIED", bool(source_locks.get("verified")), "verified" if source_locks.get("verified") else "invalid")

    reports_dir = root / "reports" / "production_acceptance"
    try:
        reports_dir.mkdir(parents=True, exist_ok=True)
        writable = os.access(reports_dir, os.W_OK)
    except OSError:
        writable = False
    record("EVIDENCE_DIRECTORY_WRITABLE", writable, "writable" if writable else "not_writable")

    try:
        disk = shutil.disk_usage(root)
        disk_detail = {"free_bytes": disk.free, "total_bytes": disk.total}
    except OSError:
        disk_detail = {"free_bytes": None, "total_bytes": None}
        problems.append("DISK_USAGE_UNAVAILABLE")
        checks["DISK_USAGE_AVAILABLE"] = {"ok": False, "detail": "unavailable"}
    else:
        checks["DISK_USAGE_AVAILABLE"] = {"ok": True, "detail": "available"}

    payload: dict[str, object] = {
        "schema_version": "1.0",
        "classification": "PRODUCTION_ACCEPTANCE_RUNNER_READINESS",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "verified": not problems,
        "problems": problems,
        "checks": checks,
        "runner_context": {
            "actions": action_markers["GITHUB_ACTIONS"].lower() == "true",
            "os": action_markers["RUNNER_OS"] or None,
            "arch": action_markers["RUNNER_ARCH"] or None,
            "name_present": bool(action_markers["RUNNER_NAME"].strip()),
        },
        "disk": disk_detail,
        "source_lock_problems": source_locks.get("problems", []),
        "truth_policy": "Runner readiness proves local execution prerequisites only. It contains no credentials and is not production acceptance evidence.",
    }
    return payload


def write_report(payload: Mapping[str, object], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Secret-free readiness check for the production-acceptance self-hosted runner")
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--require-actions-context", action="store_true")
    args = parser.parse_args()
    root = args.root.resolve()
    output = args.output if args.output.is_absolute() else root / args.output
    payload = run_readiness(root, require_actions_context=args.require_actions_context)
    write_report(payload, output)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload.get("verified") is True else 2


if __name__ == "__main__":
    raise SystemExit(main())
