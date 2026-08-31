#!/usr/bin/env bash
set -euo pipefail
: "${RESTART_DRILL_COMMAND:?Set RESTART_DRILL_COMMAND to the approved isolated runtime restart drill command.}"
: "${RESTART_EVIDENCE_JSON:?Set RESTART_EVIDENCE_JSON to the machine-readable semantic restart evidence JSON path.}"
bash -lc "$RESTART_DRILL_COMMAND"
exec python scripts/external/verify_restart_evidence.py "$RESTART_EVIDENCE_JSON"
