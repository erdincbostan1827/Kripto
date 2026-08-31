#!/usr/bin/env bash
set -euo pipefail
: "${HA_DRILL_COMMAND:?Set HA_DRILL_COMMAND to the approved isolated HA/failover drill command.}"
: "${HA_EVIDENCE_JSON:?Set HA_EVIDENCE_JSON to the drill's machine-readable evidence JSON path.}"
bash -lc "$HA_DRILL_COMMAND"
exec python scripts/external/verify_drill_evidence.py ha "$HA_EVIDENCE_JSON"
