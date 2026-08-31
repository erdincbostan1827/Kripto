from __future__ import annotations

import json
import re
import sys
from hashlib import sha256
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT = ROOT / 'reports' / 'external_acceptance' / 'scanner_image_digests.json'
REQUIRED = {'gitleaks', 'trivy', 'syft'}
DIGEST_RE = re.compile(r'^[^\s@]+@sha256:[0-9a-f]{64}$')


def verify(path: Path = DEFAULT) -> dict:
    problems: list[str] = []
    payload: dict = {}
    if not path.is_file():
        return {'verified': False, 'problems': ['SCANNER_DIGEST_RECEIPT_MISSING'], 'sha256': None, 'scanners': {}}
    raw = path.read_bytes()
    try:
        value = json.loads(raw)
        if not isinstance(value, dict):
            raise ValueError('receipt must be an object')
        payload = value
    except Exception:
        return {'verified': False, 'problems': ['SCANNER_DIGEST_RECEIPT_INVALID_JSON'], 'sha256': sha256(raw).hexdigest(), 'scanners': {}}

    if payload.get('schema_version') != '1.0':
        problems.append('SCANNER_DIGEST_SCHEMA_UNSUPPORTED')
    if payload.get('classification') != 'CI_SCANNER_IMAGE_DIGEST_RECEIPT':
        problems.append('SCANNER_DIGEST_CLASSIFICATION_INVALID')
    scanners = payload.get('scanners')
    if not isinstance(scanners, dict):
        scanners = {}
        problems.append('SCANNER_DIGEST_SCANNERS_INVALID')
    if set(scanners) != REQUIRED:
        problems.append('SCANNER_DIGEST_SET_MISMATCH')
    for name in sorted(REQUIRED):
        row = scanners.get(name)
        if not isinstance(row, dict):
            problems.append(f'SCANNER_DIGEST_ROW_MISSING:{name}')
            continue
        tag = row.get('requested_image')
        digest = row.get('resolved_digest')
        if not isinstance(tag, str) or not tag or '@sha256:' in tag:
            problems.append(f'SCANNER_REQUESTED_IMAGE_INVALID:{name}')
        if not isinstance(digest, str) or not DIGEST_RE.fullmatch(digest):
            problems.append(f'SCANNER_REPODIGEST_INVALID:{name}')
        elif isinstance(tag, str) and tag:
            requested_repo = tag.split('@', 1)[0].rsplit(':', 1)[0] if '/' in tag else tag.rsplit(':', 1)[0]
            resolved_repo = digest.split('@sha256:', 1)[0]
            # Docker Hub may canonicalize an unqualified namespace, but a digest
            # must never resolve to a different repository than the requested scanner.
            aliases = {requested_repo, resolved_repo}
            if requested_repo.startswith('docker.io/'):
                aliases.add(requested_repo[len('docker.io/'):])
            if resolved_repo.startswith('docker.io/'):
                aliases.add(resolved_repo[len('docker.io/'):])
            if requested_repo not in {resolved_repo, resolved_repo.removeprefix('docker.io/')} and resolved_repo not in {requested_repo, 'docker.io/' + requested_repo}:
                problems.append(f'SCANNER_REPOSITORY_MISMATCH:{name}')
    return {
        'verified': not problems,
        'problems': problems,
        'sha256': sha256(raw).hexdigest(),
        'scanners': scanners,
    }


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    path = Path(args[0]).resolve() if args else DEFAULT
    result = verify(path)
    print(json.dumps(result, sort_keys=True))
    return 0 if result['verified'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
