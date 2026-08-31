#!/usr/bin/env bash
set -euo pipefail
python -m compileall -q backend tests
pytest -q -W error
python scripts/preflight.py
python scripts/prohibited_scan.py
