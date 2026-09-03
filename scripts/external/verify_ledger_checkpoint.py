from __future__ import annotations

from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import sys
from typing import Iterator

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.release.evidence_ledger_checkpoint import DEFAULT_PATH, LEDGER_PATH, verify_ledger_checkpoint
from scripts.external.run_approved_drill import _run_redacted, _shell_argv

TRUST_ENV = "ACCEPTANCE_LEDGER_CHECKPOINT_VERIFY_COMMAND"


@contextmanager
def _temporary_env(updates: dict[str, str | None]) -> Iterator[None]:
    previous = {key: os.environ.get(key) for key in updates}
    try:
        for key, value in updates.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        yield
    finally:
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def _expected_environment() -> dict[str, str | None]:
    environment_id = os.environ.get("ACCEPTANCE_ENVIRONMENT_ID", "")
    topology_hash = os.environ.get("ACCEPTANCE_TOPOLOGY_HASH", "").lower() or None
    return {
        "acceptance_environment_id_hash": hashlib.sha256(environment_id.encode()).hexdigest() if environment_id else None,
        "topology_hash": topology_hash,
    }


def _append_problem(result: dict, problem: str, *, trust_status: str) -> dict:
    problems = list(result.get("problems") or [])
    if problem not in problems:
        problems.append(problem)
    return {
        **result,
        "verified": False,
        "problems": problems,
        "trust_status": trust_status,
        "trust_verified": False,
    }


def verify_with_external_trust(path: Path) -> dict:
    trust_command = os.environ.get(TRUST_ENV, "").strip()

    # The backend verifier remains authoritative for schema, freshness, ledger,
    # signature artifact, release challenge, Git SHA and environment/topology
    # bindings. Temporarily hide the external verifier command so its legacy
    # Bash invocation cannot run; this wrapper performs that single trust step
    # cross-platform after all internal bindings have passed.
    with _temporary_env({TRUST_ENV: None}):
        result = verify_ledger_checkpoint(
            path,
            root=ROOT,
            expected_environment=_expected_environment(),
            require_external_trust=False,
        )

    if not result.get("verified"):
        return result
    if not trust_command:
        return _append_problem(
            result,
            "LEDGER_CHECKPOINT_EXTERNAL_TRUST_VERIFIER_MISSING",
            trust_status="NOT_CONFIGURED",
        )

    try:
        document = json.loads(path.read_text(encoding="utf-8"))
        signature_rel = document.get("signature_artifact")
        if not isinstance(signature_rel, str) or not signature_rel:
            return _append_problem(
                result,
                "LEDGER_CHECKPOINT_SIGNATURE_BINDING_INVALID",
                trust_status="NOT_EXECUTED",
            )
        signature_path = (ROOT / signature_rel).resolve()
        signature_path.relative_to(ROOT.resolve())
        ledger_path = (ROOT / LEDGER_PATH).resolve()
        checkpoint_path = path.resolve()
        checkpoint_path.relative_to(ROOT.resolve())
        argv = _shell_argv(trust_command)
        with _temporary_env(
            {
                "ACCEPTANCE_LEDGER_CHECKPOINT_PATH": str(checkpoint_path),
                "ACCEPTANCE_LEDGER_PATH": str(ledger_path),
                "ACCEPTANCE_LEDGER_CHECKPOINT_SIGNATURE_PATH": str(signature_path),
            }
        ):
            rc = _run_redacted(argv, secret_command=trust_command)
    except (OSError, RuntimeError, ValueError, json.JSONDecodeError) as exc:
        return _append_problem(
            result,
            "LEDGER_CHECKPOINT_EXTERNAL_TRUST_ERROR",
            trust_status=f"EXTERNAL_COMMAND_ERROR:{type(exc).__name__}",
        )

    if rc != 0:
        return _append_problem(
            result,
            "LEDGER_CHECKPOINT_EXTERNAL_TRUST_FAILED",
            trust_status="EXTERNAL_COMMAND_REJECTED",
        )
    return {
        **result,
        "verified": True,
        "trust_status": "VERIFIED_BY_EXTERNAL_COMMAND",
        "trust_verified": True,
    }


def main() -> int:
    path = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else (ROOT / DEFAULT_PATH)
    result = verify_with_external_trust(path)
    print(json.dumps(result, sort_keys=True))
    return 0 if result.get("verified") else 2


if __name__ == "__main__":
    raise SystemExit(main())
