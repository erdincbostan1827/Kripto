from __future__ import annotations

import json
from pathlib import Path

from scripts.external.verify_scanner_image_digests import verify


def _receipt(path: Path) -> None:
    d = 'a' * 64
    payload = {
        'schema_version': '1.0',
        'classification': 'CI_SCANNER_IMAGE_DIGEST_RECEIPT',
        'scanners': {
            'gitleaks': {'requested_image': 'ghcr.io/gitleaks/gitleaks:v8.28.0', 'resolved_digest': f'ghcr.io/gitleaks/gitleaks@sha256:{d}'},
            'trivy': {'requested_image': 'aquasec/trivy:0.65.0', 'resolved_digest': f'aquasec/trivy@sha256:{d}'},
            'syft': {'requested_image': 'anchore/syft:v1.32.0', 'resolved_digest': f'anchore/syft@sha256:{d}'},
        },
    }
    path.write_text(json.dumps(payload))


def test_scanner_receipt_binds_requested_repository_to_digest_repository(tmp_path: Path):
    path = tmp_path / 'receipt.json'
    _receipt(path)
    assert verify(path)['verified']


def test_scanner_receipt_rejects_digest_from_different_repository(tmp_path: Path):
    path = tmp_path / 'receipt.json'
    _receipt(path)
    payload = json.loads(path.read_text())
    payload['scanners']['trivy']['resolved_digest'] = 'evil.example/other/scanner@sha256:' + 'b' * 64
    path.write_text(json.dumps(payload))
    result = verify(path)
    assert not result['verified']
    assert 'SCANNER_REPOSITORY_MISMATCH:trivy' in result['problems']
