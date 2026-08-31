#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
PYTHONPATH="backend:." pytest -q -W error tests/safety/test_faults.py | tee reports/FAULT_INJECTION_RAW.txt
python - <<'PY'
from pathlib import Path
raw=Path('reports/FAULT_INJECTION_RAW.txt').read_text(encoding='utf-8')
Path('reports/FAULT_INJECTION_REPORT.md').write_text(
    '# Fault Injection Report\n\n'
    'Status: **PASS — LOCAL MOCK/FAULT SAFETY TESTS ONLY**\n\n'
    'The suite covers local injected failure semantics. It is not evidence of real exchange, host, PostgreSQL, Redis, WAN or HA chaos acceptance.\n\n'
    '```text\n'+raw+'\n```\n', encoding='utf-8')
PY
