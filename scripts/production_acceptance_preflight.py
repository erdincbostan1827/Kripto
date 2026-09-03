from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Mapping

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.bounded_subprocess import run_captured_split

DEFAULT_OUTPUT = ROOT / "reports" / "production_acceptance" / "PRODUCTION_ACCEPTANCE_PREFLIGHT.json"

SECRET_ENV_NAMES = (
    "BINANCE_TESTNET_API_KEY",
    "BINANCE_TESTNET_API_SECRET",
    "PITR_DRILL_COMMAND",
    "PITR_EVIDENCE_JSON",
    "HA_DRILL_COMMAND",
    "HA_EVIDENCE_JSON",
    "WORM_ACCEPTANCE_COMMAND",
    "WORM_EVIDENCE_JSON",
    "RESTART_DRILL_COMMAND",
    "RESTART_EVIDENCE_JSON",
    "PROVENANCE_SIGN_VERIFY_COMMAND",
    "ACCEPTANCE_CHALLENGE_VERIFY_COMMAND",
    "LEDGER_CHECKPOINT_SIGN_COMMAND",
    "ACCEPTANCE_LEDGER_CHECKPOINT_VERIFY_COMMAND",
)

REQUIRED_TOOLS = ("git", "docker", "node", "npm", "uv", "bash")
_SHA_RE = re.compile(r"^[0-9a-f]{40,64}$")
_DIGEST_RE = re.compile(r"^[^\s@]+@sha256:[0-9a-f]{64}$")
_HEX64_RE = re.compile(r"^[0-9a-fA-F]{64}$")


def _git_sha(root: Path) -> str:
    try:
        proc = run_captured_split(["git", "rev-parse", "HEAD"], cwd=root, timeout=10)
    except Exception:
        return "UNAVAILABLE"
    value = (proc.stdout or "").strip().lower()
    return value if proc.returncode == 0 and _SHA_RE.fullmatch(value) else "UNAVAILABLE"


def _present(env: Mapping[str, str], name: str) -> bool:
    return bool(str(env.get(name, "")).strip())


def run_preflight(
    root: Path = ROOT,
    *,
    env: Mapping[str, str] | None = None,
    which: Callable[[str], str | None] = shutil.which,
) -> dict[str, object]:
    environment = dict(os.environ if env is None else env)
    checks: dict[str, dict[str, object]] = {}
    problems: list[str] = []

    def record(check_id: str, ok: bool, detail: str) -> None:
        checks[check_id] = {"ok": bool(ok), "detail": detail}
        if not ok:
            problems.append(check_id)

    actual_sha = _git_sha(root)
    expected_sha = str(environment.get("EXPECTED_ACCEPTANCE_SHA", "")).strip().lower()
    ci_sha = str(environment.get("CI_COMMIT_SHA", "")).strip().lower()

    record("GIT_IDENTITY_AVAILABLE", actual_sha != "UNAVAILABLE", "available" if actual_sha != "UNAVAILABLE" else "unavailable")
    record("EXPECTED_ACCEPTANCE_SHA_PRESENT", bool(_SHA_RE.fullmatch(expected_sha)), "present" if _SHA_RE.fullmatch(expected_sha) else "missing_or_invalid")
    record("CI_COMMIT_SHA_PRESENT", bool(_SHA_RE.fullmatch(ci_sha)), "present" if _SHA_RE.fullmatch(ci_sha) else "missing_or_invalid")
    record("GIT_SHA_MATCHES_EXPECTED", actual_sha != "UNAVAILABLE" and actual_sha == expected_sha, "matched" if actual_sha == expected_sha and actual_sha != "UNAVAILABLE" else "mismatch")
    record("CI_SHA_MATCHES_EXPECTED", bool(expected_sha) and ci_sha == expected_sha, "matched" if ci_sha == expected_sha and expected_sha else "mismatch")

    for name in ("GITHUB_REPOSITORY", "GITHUB_RUN_ID", "GITHUB_WORKFLOW_REF"):
        record(f"ENV_PRESENT:{name}", _present(environment, name), "present" if _present(environment, name) else "missing")

    digest = str(environment.get("EXPECTED_CONTAINER_DIGEST", "")).strip().lower()
    image = str(environment.get("ACCEPTANCE_CONTAINER_IMAGE", "")).strip()
    record("IMMUTABLE_CONTAINER_DIGEST_VALID", bool(_DIGEST_RE.fullmatch(digest)), "valid" if _DIGEST_RE.fullmatch(digest) else "missing_or_invalid")
    record("CONTAINER_IMAGE_PRESENT", bool(image) and not any(ch.isspace() for ch in image), "present" if image and not any(ch.isspace() for ch in image) else "missing_or_invalid")
    record("CONTAINER_IMAGE_LOWERCASE", bool(image) and image == image.lower(), "lowercase" if image and image == image.lower() else "invalid")
    record("CONTAINER_IMAGE_BOUND_TO_SHA", bool(image and expected_sha and image.endswith(f":{expected_sha}")), "bound" if image and expected_sha and image.endswith(f":{expected_sha}") else "mismatch")

    receipt = root / "reports" / "CI_CONTAINER_REPODIGEST_VERIFIED.txt"
    receipt_value = receipt.read_text(encoding="utf-8").strip().lower() if receipt.is_file() else ""
    record("VERIFIED_CONTAINER_DIGEST_RECEIPT_PRESENT", bool(receipt_value), "present" if receipt_value else "missing")
    record("VERIFIED_CONTAINER_DIGEST_RECEIPT_MATCH", bool(digest and receipt_value == digest), "matched" if digest and receipt_value == digest else "mismatch")

    env_id = str(environment.get("ACCEPTANCE_ENVIRONMENT_ID", "")).strip()
    topology_hash = str(environment.get("ACCEPTANCE_TOPOLOGY_HASH", "")).strip()
    record("ACCEPTANCE_ENVIRONMENT_ID_PRESENT", bool(env_id), "present" if env_id else "missing")
    record("ACCEPTANCE_TOPOLOGY_HASH_VALID", bool(_HEX64_RE.fullmatch(topology_hash)), "valid" if _HEX64_RE.fullmatch(topology_hash) else "missing_or_invalid")

    trust_required = str(environment.get("ACCEPTANCE_REQUIRE_CHALLENGE_TRUST", "")).strip().lower() in {"1", "true", "yes"}
    record("CHALLENGE_TRUST_REQUIRED", trust_required, "required" if trust_required else "not_required")
    record("CHALLENGE_VERIFY_COMMAND_PRESENT", _present(environment, "ACCEPTANCE_CHALLENGE_VERIFY_COMMAND"), "present" if _present(environment, "ACCEPTANCE_CHALLENGE_VERIFY_COMMAND") else "missing")
    record("BINANCE_TESTNET_EXECUTION_EXPLICIT", str(environment.get("BINANCE_TESTNET_EXECUTE", "")).strip() == "YES", "enabled" if str(environment.get("BINANCE_TESTNET_EXECUTE", "")).strip() == "YES" else "not_enabled")

    for name in SECRET_ENV_NAMES:
        record(f"SECRET_PRESENT:{name}", _present(environment, name), "present_redacted" if _present(environment, name) else "missing")

    for tool in REQUIRED_TOOLS:
        available = which(tool) is not None
        record(f"TOOL_AVAILABLE:{tool}", available, "available" if available else "missing")

    record("PYTHON_EXECUTABLE_AVAILABLE", bool(sys.executable and Path(sys.executable).exists()), "available" if sys.executable and Path(sys.executable).exists() else "missing")

    payload: dict[str, object] = {
        "schema_version": "1.0",
        "classification": "PRODUCTION_ACCEPTANCE_REAL_TARGET_PREFLIGHT",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "git_commit_sha": actual_sha,
        "acceptance_expected_git_sha": expected_sha or None,
        "checks": checks,
        "verified": not problems,
        "problems": problems,
        "redaction_policy": "values_omitted",
        "truth_policy": "Preflight validates prerequisite presence and identity only. It never serializes sensitive input values and never substitutes for the real acceptance drills, external trust verification, or release gate.",
    }
    return payload


def write_report(payload: Mapping[str, object], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Fail-closed preflight for the self-hosted production acceptance target")
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    root = args.root.resolve()
    output = args.output
    if not output.is_absolute():
        output = root / output
    payload = run_preflight(root)
    write_report(payload, output)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload.get("verified") is True else 2


if __name__ == "__main__":
    raise SystemExit(main())
