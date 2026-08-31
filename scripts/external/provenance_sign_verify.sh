#!/usr/bin/env bash
set -euo pipefail
: "${PROVENANCE_SIGN_VERIFY_COMMAND:?Set PROVENANCE_SIGN_VERIFY_COMMAND to the approved signing + verification command for the target CI.}"
# The approved command must create both a detached signature artefact and
# reports/external_acceptance/provenance_signature_verification.json using schema 2.0,
# bound to the current trusted release challenge and ACCEPTANCE_ENVIRONMENT_ID /
# ACCEPTANCE_TOPOLOGY_HASH.
bash -lc "$PROVENANCE_SIGN_VERIFY_COMMAND"
python scripts/external/verify_provenance_signature.py
