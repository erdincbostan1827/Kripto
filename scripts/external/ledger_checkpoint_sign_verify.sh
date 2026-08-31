#!/usr/bin/env bash
set -euo pipefail
: "${LEDGER_CHECKPOINT_SIGN_COMMAND:?Set LEDGER_CHECKPOINT_SIGN_COMMAND to the approved KMS/HSM/WORM checkpoint signing command.}"
: "${ACCEPTANCE_LEDGER_CHECKPOINT_VERIFY_COMMAND:?Set ACCEPTANCE_LEDGER_CHECKPOINT_VERIFY_COMMAND to the approved detached-signature verification command.}"
# The signing command must create reports/external_acceptance/evidence_ledger_checkpoint.json
# and its declared detached signature artifact. The verifier then re-binds that receipt
# to the current ledger head, trusted release challenge, Git SHA and acceptance topology.
bash -lc "$LEDGER_CHECKPOINT_SIGN_COMMAND"
exec python scripts/external/verify_ledger_checkpoint.py
