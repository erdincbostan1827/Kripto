from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.release.evidence_ledger_checkpoint import DEFAULT_PATH
from scripts.acceptance_diagnostics import classify_blocker
from scripts.external.run_approved_drill import _required_env, _run_redacted, _shell_argv
from scripts.external.verify_ledger_checkpoint import verify_with_external_trust


def main() -> int:
    try:
        signing_command = _required_env("LEDGER_CHECKPOINT_SIGN_COMMAND")
        # Explicit platform shell argv is selected by the already-hardened
        # approved-command launcher. shell=True is never used, and the command
        # value is registered as a redaction secret before output is emitted.
        argv = _shell_argv(signing_command)
        rc = _run_redacted(argv, secret_command=signing_command)
        if rc != 0:
            blocker = classify_blocker("", rc, tool=Path(argv[0]).name)
            print(json.dumps({"status": "BLOCKED", "error": "LEDGER_CHECKPOINT_SIGN_COMMAND_FAILED", "blocker": blocker}, sort_keys=True))
            return 2

        checkpoint = ROOT / DEFAULT_PATH
        result = verify_with_external_trust(checkpoint)
        print(json.dumps(result, sort_keys=True))
        return 0 if result.get("verified") else 2
    except RuntimeError as exc:
        # Runtime errors contain stable configuration/shell identifiers only;
        # never include the approved signing command value.
        print(json.dumps({"status": "BLOCKED", "error": str(exc)}, sort_keys=True))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
