from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[2]
MATRIX = ROOT / 'REQUIREMENTS_TRACEABILITY_MATRIX.yaml'
OUT = ROOT / 'reports' / 'EXTERNAL_ACCEPTANCE_EXECUTION_MAP.json'


def classify(section: int, description: str) -> str:
    t = description.lower()
    if section == 1:
        return 'dependency-locks'
    if section in {20, 43, 136}:
        return 'testnet-campaigns'
    if section in {42, 46}:
        return 'runtime'
    if section == 65:
        if 'testnet' in t or 'paper trading' in t:
            return 'testnet-campaigns'
        return 'runtime'
    if section == 96:
        return 'supply-chain'
    if section == 97:
        return 'provenance'
    if section == 99:
        return 'restart-drills'
    if section in {167, 168}:
        return 'frontend-browser'
    if section == 169:
        return 'desktop-build' if 'installer' in t or 'package' in t else 'frontend-browser'
    if section == 178:
        return 'pitr'
    if section == 181:
        return 'worm'
    if section == 184:
        return 'ha'
    if section == 189:
        if 'sign' in t:
            return 'signing'
        return 'provenance'
    raise ValueError(f'Unmapped external requirement section={section}: {description}')


COMMANDS = {
    'dependency-locks': 'python scripts/external_acceptance_runner.py --profile locks --confirm-real-target',
    'runtime': 'python scripts/external_acceptance_runner.py --profile runtime --confirm-real-target',
    'restart-drills': 'python scripts/external_acceptance_runner.py --profile restart-drills --confirm-real-target',
    'supply-chain': 'python scripts/external_acceptance_runner.py --profile supply-chain --confirm-real-target',
    'pitr': 'python scripts/external_acceptance_runner.py --profile pitr --confirm-real-target',
    'ha': 'python scripts/external_acceptance_runner.py --profile ha --confirm-real-target',
    'worm': 'python scripts/external_acceptance_runner.py --profile worm --confirm-real-target',
    'testnet-campaigns': 'python scripts/external_acceptance_runner.py --profile testnet --confirm-real-target && python scripts/external_acceptance_runner.py --profile campaigns --confirm-real-target',
    'provenance': 'python scripts/external_acceptance_runner.py --profile provenance --confirm-real-target',
    'frontend-browser': 'python scripts/external/frontend_browser_acceptance.py --confirm-real-target',
    'desktop-build': 'python scripts/external/tauri_build_readiness.py --confirm-real-target',
    'signing': 'python scripts/external_acceptance_runner.py --profile provenance --confirm-real-target',
}


def build() -> dict:
    doc = yaml.safe_load(MATRIX.read_text(encoding='utf-8'))
    rows = [r for r in doc['requirements'] if r.get('status') == 'NOT_TESTED']
    mapped = []
    for r in rows:
        profile = classify(int(r['section']), str(r.get('description', '')))
        mapped.append({
            'requirement_id': r['requirement_id'],
            'section': int(r['section']),
            'priority': r['priority'],
            'description': r['description'],
            'profile': profile,
            'command': COMMANDS[profile],
            'classification': 'EXECUTION_PLAN_NOT_ACCEPTANCE_EVIDENCE',
        })
    counts = Counter(x['profile'] for x in mapped)
    payload = {
        'schema_version': '1.0',
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'classification': 'EXTERNAL_ACCEPTANCE_EXECUTION_MAP_NOT_ACCEPTANCE_EVIDENCE',
        'truth_policy': 'This map schedules unresolved requirements only. It cannot promote any requirement to PASS; only checksum-bound real external acceptance evidence may do so.',
        'open_requirement_count': len(rows),
        'mapped_requirement_count': len(mapped),
        'unmapped_requirement_count': len(rows) - len(mapped),
        'profiles': dict(sorted(counts.items())),
        'requirements': mapped,
    }
    return payload


def main() -> int:
    payload = build()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload['unmapped_requirement_count'] == 0 else 2


if __name__ == '__main__':
    raise SystemExit(main())
