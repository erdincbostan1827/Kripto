#!/usr/bin/env bash
set -euo pipefail
: "${PITR_DRILL_COMMAND:?Set PITR_DRILL_COMMAND to the approved isolated restore-drill command.}"
: "${PITR_EVIDENCE_JSON:?Set PITR_EVIDENCE_JSON to the drill's machine-readable evidence JSON path.}"
bash -lc "$PITR_DRILL_COMMAND"
exec python scripts/external/verify_drill_evidence.py pitr "$PITR_EVIDENCE_JSON"
