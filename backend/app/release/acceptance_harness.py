from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from hashlib import sha256
import json
import shutil
import subprocess


@dataclass(frozen=True)
class AcceptanceAttempt:
    key: str
    command: tuple[str, ...]
    tool_available: bool
    exit_code: int | None
    real_system: bool
    status: str
    evidence_path: str
    evidence_sha256: str
    observed_at: str
    blocker: str | None = None


def _sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def run_command_attempt(*, key: str, command: list[str], root: Path, evidence_dir: Path,
                        real_system: bool, timeout_seconds: int = 120) -> AcceptanceAttempt:
    evidence_dir.mkdir(parents=True, exist_ok=True)
    tool = command[0]
    available = shutil.which(tool) is not None
    path = evidence_dir / f"{key}.log"
    observed = datetime.now(timezone.utc).isoformat()
    if not available:
        path.write_text(f"tool unavailable: {tool}\n", encoding="utf-8")
        return AcceptanceAttempt(key, tuple(command), False, None, real_system, "BLOCKED",
                                 str(path.relative_to(root)), _sha(path), observed, f"TOOL_UNAVAILABLE:{tool}")
    try:
        proc = subprocess.run(command, cwd=root, text=True, stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT, timeout=timeout_seconds, check=False)
        path.write_text(proc.stdout or "", encoding="utf-8")
        ok = proc.returncode == 0 and real_system
        blocker = None if ok else ("SIMULATED_NOT_EXTERNAL_ACCEPTANCE" if proc.returncode == 0 else f"EXIT_CODE:{proc.returncode}")
        return AcceptanceAttempt(key, tuple(command), True, proc.returncode, real_system,
                                 "PASS" if ok else "BLOCKED", str(path.relative_to(root)),
                                 _sha(path), observed, blocker)
    except subprocess.TimeoutExpired as exc:
        out = (exc.stdout or "") + "\nTIMEOUT\n"
        path.write_text(out, encoding="utf-8")
        return AcceptanceAttempt(key, tuple(command), True, None, real_system, "BLOCKED",
                                 str(path.relative_to(root)), _sha(path), observed, "TIMEOUT")


def write_attempt_manifest(attempts: list[AcceptanceAttempt], output: Path) -> dict:
    payload = {
        "schema_version": "1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "truth_policy": "Only exit-code-0 evidence executed against the declared real system can satisfy external acceptance.",
        "attempts": [asdict(a) for a in attempts],
        "all_pass": bool(attempts) and all(a.status == "PASS" for a in attempts),
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload
