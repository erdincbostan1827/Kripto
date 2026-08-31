from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.generate_release_manifest import SOURCE_ROOTS

OUT = ROOT / 'reports/LOCAL_SOURCE_PROVENANCE.json'


def run(*args: str, root: Path = ROOT) -> str:
    return subprocess.check_output(args, cwd=root, text=True, stderr=subprocess.DEVNULL).strip()


def collect(*, root: Path = ROOT, source_roots: list[str] | tuple[str, ...] = tuple(SOURCE_ROOTS)) -> dict:
    try:
        sha = run('git', 'rev-parse', 'HEAD', root=root)
        status_args = ['git', 'status', '--porcelain', '--untracked-files=all', '--', *source_roots]
        dirty_rows = [row for row in run(*status_args, root=root).splitlines() if row.strip()]
        tags = run('git', 'tag', '--points-at', 'HEAD', root=root).splitlines()
    except Exception:
        sha = 'UNAVAILABLE'
        dirty_rows = ['GIT_STATUS_UNAVAILABLE']
        tags = []
    return {
        'schema_version': '1.1',
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'git_commit_sha': sha,
        'clean_tree': not dirty_rows,
        'dirty_source_entries': dirty_rows,
        'source_scope': list(source_roots),
        'tags_at_head': tags,
        'immutable_tag_present': any(t.startswith('v0.3.0-phase') for t in tags),
        'classification': 'LOCAL_SOURCE_PROVENANCE_NOT_CI_PROVENANCE',
    }


def main() -> int:
    d = collect()
    OUT.write_text(json.dumps(d, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    print(json.dumps(d))
    return 0 if d['git_commit_sha'] != 'UNAVAILABLE' else 1


if __name__ == '__main__':
    raise SystemExit(main())
