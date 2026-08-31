#!/usr/bin/env bash
set -euo pipefail
: "${WORM_ACCEPTANCE_COMMAND:?Set WORM_ACCEPTANCE_COMMAND to the approved WORM storage acceptance command.}"
: "${WORM_EVIDENCE_JSON:?Set WORM_EVIDENCE_JSON to the machine-readable evidence JSON path.}"
bash -lc "$WORM_ACCEPTANCE_COMMAND"
exec python scripts/external/verify_drill_evidence.py worm "$WORM_EVIDENCE_JSON"
