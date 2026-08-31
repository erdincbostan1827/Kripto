from __future__ import annotations
import argparse, json, re, subprocess, sys
from pathlib import Path

HEX40 = re.compile(r'^[0-9a-fA-F]{40}$')

def git(*args: str) -> str:
    return subprocess.check_output(['git', *args], text=True).strip()

def validate(ref: str) -> dict:
    head = git('rev-parse', 'HEAD')
    if HEX40.fullmatch(ref):
        resolved = git('rev-parse', ref)
        if resolved != head:
            raise ValueError('ACCEPTANCE_SHA_DOES_NOT_MATCH_CHECKED_OUT_HEAD')
        return {'status':'PASS','kind':'FULL_COMMIT_SHA','input_ref':ref,'resolved_sha':resolved}
    # Tags only; branches and other symbolic refs are rejected.
    tag_ref = f'refs/tags/{ref}'
    try:
        obj_type = git('cat-file','-t',tag_ref)
    except subprocess.CalledProcessError as e:
        raise ValueError('ACCEPTANCE_REF_MUST_BE_FULL_SHA_OR_EXISTING_TAG') from e
    if obj_type != 'tag':
        raise ValueError('ACCEPTANCE_TAG_MUST_BE_ANNOTATED')
    resolved = git('rev-list','-n','1',tag_ref)
    if resolved != head:
        raise ValueError('ACCEPTANCE_TAG_DOES_NOT_MATCH_CHECKED_OUT_HEAD')
    return {'status':'PASS','kind':'ANNOTATED_TAG','input_ref':ref,'resolved_sha':resolved}

def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument('ref')
    ap.add_argument('--output', default='reports/ACCEPTANCE_REF_VALIDATION.json')
    ns=ap.parse_args()
    try:
        data=validate(ns.ref)
        rc=0
    except Exception as exc:
        data={'status':'BLOCKED','input_ref':ns.ref,'error':str(exc)}
        rc=2
    p=Path(ns.output); p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=2, sort_keys=True)+'\n')
    print(json.dumps(data, sort_keys=True))
    return rc
if __name__=='__main__':
    raise SystemExit(main())
