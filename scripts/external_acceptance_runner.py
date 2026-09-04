from __future__ import annotations

import argparse
import json
import os
import platform
import shlex
import shutil
import subprocess
import sys
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
for search_root in (ROOT, BACKEND):
    search_root_text = str(search_root)
    if search_root_text not in sys.path:
        sys.path.insert(0, search_root_text)
REPORTS = ROOT / "reports" / "external_acceptance"
GIT_PROBE_TIMEOUT_SECONDS = 10

from backend.app.release.acceptance_challenge import verify_challenge
from backend.app.release.acceptance_contract import RUNNER_GROUP_KEYS, build_plan, command_contract, command_contract_sha256
from backend.app.release.evidence_ledger import append_entry
from scripts.acceptance_diagnostics import classify_blocker, redact_text
from scripts.bounded_subprocess import run_captured, run_captured_split


@dataclass(frozen=True)
class Evidence:
    key: str
    status: str
    real_system: bool
    command: tuple[str, ...]
    exit_code: int | None
    blocker: str | None
    artifact: str
    sha256: str
    observed_at: str


def _sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _run(key: str, command: list[str], *, real_system: bool, run_dir: Path | None = None, timeout: int = 300) -> Evidence:
    run_dir = run_dir or (REPORTS / "adhoc")
    run_dir.mkdir(parents=True, exist_ok=True)
    log = run_dir / f"{key}.log"
    observed = datetime.now(timezone.utc).isoformat()
    tool = command[0]
    if shutil.which(tool) is None:
        _write(log, f"BLOCKED: tool unavailable: {tool}\n")
        return Evidence(key, "BLOCKED", real_system, tuple(command), None,
                        f"TOOL_UNAVAILABLE:{tool}", str(log.relative_to(ROOT)), _sha(log), observed)
    try:
        proc = run_captured(command, cwd=ROOT, timeout=timeout)
        safe_output = redact_text(proc.stdout or "")
        _write(log, safe_output)
        if proc.returncode != 0:
            status, blocker = "BLOCKED", classify_blocker(safe_output, proc.returncode, tool=tool)
        elif not real_system:
            status, blocker = "BLOCKED", "SIMULATED_NOT_EXTERNAL_ACCEPTANCE"
        else:
            status, blocker = "PASS", None
        return Evidence(key, status, real_system, tuple(command), proc.returncode, blocker,
                        str(log.relative_to(ROOT)), _sha(log), observed)
    except subprocess.TimeoutExpired as exc:
        out = exc.stdout or ""
        if isinstance(out, bytes):
            out = out.decode(errors="replace")
        _write(log, redact_text(out) + "\nTIMEOUT\n")
        return Evidence(key, "BLOCKED", real_system, tuple(command), None, "COMMAND_OR_NETWORK_TIMEOUT",
                        str(log.relative_to(ROOT)), _sha(log), observed)


def _presence(key: str, rel: str, *, run_dir: Path) -> Evidence:
    p = ROOT / rel
    observed = datetime.now(timezone.utc).isoformat()
    log = run_dir / f"{key}.log"
    if p.is_file():
        _write(log, f"present: {rel}\nsha256: {_sha(p)}\n")
        return Evidence(key, "PASS", True, tuple(), 0, None, str(log.relative_to(ROOT)), _sha(log), observed)
    _write(log, f"BLOCKED: missing: {rel}\n")
    return Evidence(key, "BLOCKED", True, tuple(), None, f"MISSING:{rel}",
                    str(log.relative_to(ROOT)), _sha(log), observed)


def _credential_guard() -> tuple[bool, str]:
    names = ("BINANCE_TESTNET_API_KEY", "BINANCE_TESTNET_API_SECRET")
    missing = [n for n in names if not os.getenv(n)]
    return (not missing, "PRESENT_REDACTED" if not missing else "MISSING:" + ",".join(missing))


def _git_sha() -> str:
    try:
        proc = run_captured_split(["git", "rev-parse", "HEAD"], cwd=ROOT, timeout=GIT_PROBE_TIMEOUT_SECONDS)
    except (subprocess.TimeoutExpired, OSError):
        return "UNAVAILABLE"
    value = (proc.stdout or "").strip()
    return value if proc.returncode == 0 and value else "UNAVAILABLE"


def _environment() -> dict:
    git_sha = _git_sha()
    env_id = os.getenv("ACCEPTANCE_ENVIRONMENT_ID", "")
    topology_hash = os.getenv("ACCEPTANCE_TOPOLOGY_HASH", "")
    return {
        "hostname_hash": sha256(platform.node().encode()).hexdigest()[:16],
        "platform": platform.platform(),
        "python": platform.python_version(),
        "git_commit_sha": git_sha,
        "acceptance_environment_id_hash": sha256(env_id.encode()).hexdigest() if env_id else None,
        "topology_hash": topology_hash.lower() if len(topology_hash) == 64 and all(c in "0123456789abcdefABCDEF" for c in topology_hash) else None,
    }


def _group_status(evidence: list[Evidence]) -> dict[str, str]:
    by_key = {e.key: e.status for e in evidence}
    definitions = RUNNER_GROUP_KEYS
    result: dict[str, str] = {}
    for group, keys in definitions.items():
        present = [by_key[k] for k in keys if k in by_key]
        if not present:
            result[group] = "NOT_TESTED"
        elif len(present) == len(keys) and all(status == "PASS" for status in present):
            result[group] = "PASS"
        else:
            result[group] = "BLOCKED"
    return result


def execute(profile: str, *, confirm_real: bool, timeout: int) -> dict:
    evidence: list[Evidence] = []
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ") + "-" + uuid.uuid4().hex[:8]
    run_dir = REPORTS / "runs" / run_id / profile
    run_dir.mkdir(parents=True, exist_ok=True)
    # Phase 163: real aggregate acceptance is produced only by the merge path.
    # That path emits schema 4.1, appends the all-merged ledger entry and then
    # requires an externally signed ledger checkpoint.  Running profile=all
    # directly would otherwise create a schema 3.2 aggregate that can never
    # satisfy the production checkpoint contract.
    if confirm_real and profile == "all":
        payload = {
            "schema_version": "3.2",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "classification": "EXTERNAL_ACCEPTANCE_EVIDENCE_BUNDLE",
            "truth_policy": "Real aggregate acceptance must be assembled by merge_external_acceptance and verified under schema 4.1 with a signed ledger checkpoint.",
            "profile": profile,
            "command_contract_sha256": command_contract_sha256(profile),
            "run_id": run_id,
            "real_target_explicitly_confirmed": True,
            "challenge": {"verified": False, "problems": ["AGGREGATE_REAL_ACCEPTANCE_REQUIRES_MERGE"]},
            "environment": _environment(),
            "credentials": {"binance_testnet": "NOT_EVALUATED"},
            "evidence": [],
            "groups": _group_status([]),
            "selected_all_pass": False,
            "blocker": "AGGREGATE_REAL_ACCEPTANCE_REQUIRES_MERGE",
        }
        immutable_manifest = run_dir / "manifest.json"
        _write(immutable_manifest, json.dumps(payload, indent=2, sort_keys=True) + "\n")
        manifest = REPORTS / "manifest_all.json"
        _write(manifest, immutable_manifest.read_text(encoding="utf-8"))
        payload["manifest_sha256"] = _sha(immutable_manifest)
        payload["immutable_manifest"] = str(immutable_manifest.relative_to(ROOT))
        return payload
    challenge_path = REPORTS / "release_challenge.json"
    challenge = verify_challenge(challenge_path, root=ROOT, require_trust=True if confirm_real else False)
    if confirm_real and not challenge.get("verified"):
        payload = {
            "schema_version": "3.2",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "classification": "EXTERNAL_ACCEPTANCE_EVIDENCE_BUNDLE",
            "truth_policy": "Real external acceptance requires a fresh release-bound challenge before any acceptance command executes.",
            "profile": profile,
            "command_contract_sha256": command_contract_sha256(profile),
            "run_id": run_id,
            "real_target_explicitly_confirmed": True,
            "challenge": challenge,
            "environment": _environment(),
            "credentials": {"binance_testnet": "NOT_EVALUATED"},
            "evidence": [],
            "groups": _group_status([]),
            "selected_all_pass": False,
            "blocker": "RELEASE_CHALLENGE_NOT_VERIFIED",
        }
        immutable_manifest = run_dir / "manifest.json"
        _write(immutable_manifest, json.dumps(payload, indent=2, sort_keys=True) + "\n")
        manifest = REPORTS / f"manifest_{profile}.json"
        _write(manifest, immutable_manifest.read_text(encoding="utf-8"))
        payload["manifest_sha256"] = _sha(immutable_manifest)
        payload["immutable_manifest"] = str(immutable_manifest.relative_to(ROOT))
        return payload

    if confirm_real:
        env_identity = _environment()
        missing_identity = []
        if env_identity.get("git_commit_sha") == "UNAVAILABLE":
            missing_identity.append("GIT_COMMIT_SHA")
        if not env_identity.get("acceptance_environment_id_hash"):
            missing_identity.append("ACCEPTANCE_ENVIRONMENT_ID")
        if not env_identity.get("topology_hash"):
            missing_identity.append("ACCEPTANCE_TOPOLOGY_HASH")
        if missing_identity:
            payload = {
                "schema_version": "3.2",
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "classification": "EXTERNAL_ACCEPTANCE_EVIDENCE_BUNDLE",
                "truth_policy": "Real external acceptance is bound to an explicit target environment identity and topology hash.",
                "profile": profile,
                "command_contract_sha256": command_contract_sha256(profile),
                "run_id": run_id,
                "real_target_explicitly_confirmed": True,
                "challenge": challenge,
                "environment": env_identity,
                "credentials": {"binance_testnet": "NOT_EVALUATED"},
                "evidence": [],
                "groups": _group_status([]),
                "selected_all_pass": False,
                "blocker": "ACCEPTANCE_ENVIRONMENT_IDENTITY_MISSING:" + ",".join(missing_identity),
            }
            immutable_manifest = run_dir / "manifest.json"
            _write(immutable_manifest, json.dumps(payload, indent=2, sort_keys=True) + "\n")
            manifest = REPORTS / f"manifest_{profile}.json"
            _write(manifest, immutable_manifest.read_text(encoding="utf-8"))
            payload["manifest_sha256"] = _sha(immutable_manifest)
            payload["immutable_manifest"] = str(immutable_manifest.relative_to(ROOT))
            return payload

    evidence.extend([_presence("uv_lock_file", "uv.lock", run_dir=run_dir), _presence("npm_lock_file", "frontend/package-lock.json", run_dir=run_dir)])

    creds_ok, creds_detail = _credential_guard()
    cred_log = run_dir / "credential_guard.log"
    _write(cred_log, creds_detail + "\n")
    evidence.append(Evidence("credential_guard", "PASS" if creds_ok else "BLOCKED", True, tuple(),
                             0 if creds_ok else None, None if creds_ok else creds_detail,
                             str(cred_log.relative_to(ROOT)), _sha(cred_log), datetime.now(timezone.utc).isoformat()))

    for key, command, requires_real in build_plan(profile):
        if key == "binance_testnet" and not creds_ok:
            log = run_dir / f"{key}.log"
            _write(log, "BLOCKED: TESTNET credentials missing; values are never recorded.\n")
            evidence.append(Evidence(key, "BLOCKED", True, tuple(command), None, "TESTNET_CREDENTIALS_MISSING",
                                     str(log.relative_to(ROOT)), _sha(log), datetime.now(timezone.utc).isoformat()))
            continue
        real = bool(confirm_real and requires_real)
        evidence.append(_run(key, command, real_system=real, run_dir=run_dir, timeout=timeout))

    selected_keys = {k for k, _, _ in build_plan(profile)}
    selected = [e for e in evidence if e.key in selected_keys]
    payload = {
        "schema_version": "3.2",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "classification": "EXTERNAL_ACCEPTANCE_EVIDENCE_BUNDLE",
        "truth_policy": "PASS requires exit code 0, an explicitly confirmed real target system, and hashed evidence. Missing tools, credentials, locks, or simulations remain BLOCKED.",
        "profile": profile,
        "command_contract_sha256": command_contract_sha256(profile),
        "run_id": run_id,
        "real_target_explicitly_confirmed": confirm_real,
        "challenge": challenge if confirm_real else {"verified": False, "problems": ["NOT_REQUIRED_FOR_SIMULATION"]},
        "environment": _environment(),
        "credentials": {"binance_testnet": creds_detail},
        "evidence": [asdict(e) for e in evidence],
        "groups": _group_status(evidence),
        "selected_all_pass": bool(selected) and all(e.status == "PASS" for e in selected),
    }
    immutable_manifest = run_dir / "manifest.json"
    _write(immutable_manifest, json.dumps(payload, indent=2, sort_keys=True) + "\n")
    manifest_sha = _sha(immutable_manifest)
    manifest = REPORTS / f"manifest_{profile}.json"
    _write(manifest, immutable_manifest.read_text(encoding="utf-8"))
    payload["manifest_sha256"] = manifest_sha
    payload["immutable_manifest"] = str(immutable_manifest.relative_to(ROOT))
    if payload["selected_all_pass"] and confirm_real:
        env = payload["environment"]
        append_entry(
            REPORTS / "evidence_ledger.json",
            manifest_sha256=manifest_sha,
            challenge_id=str(challenge.get("challenge_id")),
            git_commit_sha=str(env.get("git_commit_sha")),
            profile=profile,
            root=ROOT,
        )
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Fail-closed external acceptance evidence runner")
    parser.add_argument("--profile", choices=("locks", "runtime", "restart-drills", "supply-chain", "pitr", "ha", "worm", "testnet", "provenance", "campaigns", "all"), default="all")
    parser.add_argument("--confirm-real-target", action="store_true",
                        help="Explicitly attest that commands execute against the intended isolated real acceptance environment.")
    parser.add_argument("--timeout", type=int, default=300)
    args = parser.parse_args()
    payload = execute(args.profile, confirm_real=args.confirm_real_target, timeout=max(1, args.timeout))
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload["selected_all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
