from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.acceptance_diagnostics import classify_blocker, redact_text  # noqa: E402


@dataclass(frozen=True)
class DrillConfig:
    command_env: str
    evidence_env: str | None
    verifier: tuple[str, ...]


DRILLS: dict[str, DrillConfig] = {
    "restart-drills": DrillConfig(
        command_env="RESTART_DRILL_COMMAND",
        evidence_env="RESTART_EVIDENCE_JSON",
        verifier=("scripts/external/verify_restart_evidence.py", "{evidence}"),
    ),
    "pitr": DrillConfig(
        command_env="PITR_DRILL_COMMAND",
        evidence_env="PITR_EVIDENCE_JSON",
        verifier=("scripts/external/verify_drill_evidence.py", "pitr", "{evidence}"),
    ),
    "ha": DrillConfig(
        command_env="HA_DRILL_COMMAND",
        evidence_env="HA_EVIDENCE_JSON",
        verifier=("scripts/external/verify_drill_evidence.py", "ha", "{evidence}"),
    ),
    "worm": DrillConfig(
        command_env="WORM_ACCEPTANCE_COMMAND",
        evidence_env="WORM_EVIDENCE_JSON",
        verifier=("scripts/external/verify_drill_evidence.py", "worm", "{evidence}"),
    ),
    "provenance": DrillConfig(
        command_env="PROVENANCE_SIGN_VERIFY_COMMAND",
        evidence_env=None,
        verifier=("scripts/external/verify_provenance_signature.py",),
    ),
}


def _required_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"REQUIRED_ACCEPTANCE_ENV_MISSING:{name}")
    return value


def _shell_argv(
    command: str,
    *,
    platform_name: str | None = None,
    which: Callable[[str], str | None] = shutil.which,
) -> list[str]:
    platform_name = os.name if platform_name is None else platform_name
    if platform_name == "nt":
        executable = which("pwsh") or which("powershell")
        if not executable:
            raise RuntimeError("APPROVED_COMMAND_SHELL_UNAVAILABLE:POWERSHELL")
        return [executable, "-NoLogo", "-NoProfile", "-NonInteractive", "-Command", command]
    executable = which("bash")
    if not executable:
        raise RuntimeError("APPROVED_COMMAND_SHELL_UNAVAILABLE:BASH")
    return [executable, "-lc", command]


def _run_redacted(argv: list[str], *, secret_command: str | None = None) -> int:
    redaction_env = dict(os.environ)
    if secret_command:
        redaction_env["APPROVED_COMMAND_SECRET"] = secret_command
    try:
        proc = subprocess.run(
            argv,
            cwd=ROOT,
            env=os.environ.copy(),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
    except OSError as exc:
        raise RuntimeError(f"ACCEPTANCE_PROCESS_UNAVAILABLE:{type(exc).__name__}") from exc
    output = redact_text(proc.stdout or "", redaction_env)
    if output:
        print(output, end="" if output.endswith("\n") else "\n")
    return proc.returncode


def _verifier_argv(config: DrillConfig, evidence: str | None) -> list[str]:
    args: list[str] = []
    for value in config.verifier:
        if value == "{evidence}":
            if evidence is None:
                raise RuntimeError("ACCEPTANCE_EVIDENCE_PATH_MISSING")
            args.append(evidence)
        else:
            args.append(value)
    return [sys.executable, *args]


def run_profile(profile: str) -> int:
    config = DRILLS.get(profile)
    if config is None:
        raise RuntimeError(f"UNSUPPORTED_EXTERNAL_DRILL_PROFILE:{profile}")
    command = _required_env(config.command_env)
    evidence = _required_env(config.evidence_env) if config.evidence_env else None

    approved_argv = _shell_argv(command)
    command_rc = _run_redacted(approved_argv, secret_command=command)
    if command_rc != 0:
        blocker = classify_blocker("", command_rc, tool=Path(approved_argv[0]).name)
        raise RuntimeError(f"APPROVED_COMMAND_FAILED:{profile}:{blocker}")

    verifier_rc = _run_redacted(_verifier_argv(config, evidence))
    if verifier_rc != 0:
        raise RuntimeError(f"ACCEPTANCE_EVIDENCE_VERIFICATION_FAILED:{profile}:EXIT_CODE:{verifier_rc}")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 1:
        print(json.dumps({"status": "BLOCKED", "error": "exactly one external drill profile is required"}, sort_keys=True))
        return 2
    profile = args[0]
    try:
        return run_profile(profile)
    except RuntimeError as exc:
        print(json.dumps({"status": "BLOCKED", "profile": profile, "error": str(exc)}, sort_keys=True))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
