from __future__ import annotations
import hashlib, json, re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
import yaml

try:
 from scripts.test_inventory import read_verified as read_test_inventory
except ModuleNotFoundError:
 from test_inventory import read_verified as read_test_inventory

try:
 from scripts.release_gate import REQUIRED_EXTERNAL_ACCEPTANCE
 from scripts.verify_source_locks import verify_source_locks
except ModuleNotFoundError:
 from release_gate import REQUIRED_EXTERNAL_ACCEPTANCE
 from verify_source_locks import verify_source_locks

ROOT=Path(__file__).resolve().parents[1]
MATRIX=ROOT/'requirements_acceptance_matrix.yaml'
MANIFEST=ROOT/'RELEASE_MANIFEST.json'
OUT_JSON=ROOT/'reports/PROJECT_STATUS.json'
OUT_MD=ROOT/'reports/KNOWN_ISSUES_LIMITATIONS.md'

def sha256(p:Path)->str:
 h=hashlib.sha256(); h.update(p.read_bytes()); return h.hexdigest()

def test_count()->int|None:
 machine=read_test_inventory(ROOT)
 if machine.get('verified'): return machine.get('test_count')
 p=ROOT/'reports/TEST_COUNT.txt'
 if not p.exists(): return None
 text=p.read_text(encoding='utf-8',errors='ignore')
 m=re.search(r'(\d+) tests collected',text)
 if m: return int(m.group(1))
 stripped=text.strip()
 if re.fullmatch(r'\d+',stripped): return int(stripped)
 grouped=re.findall(r'^tests/.+?:\s+(\d+)\s*$',text,re.M)
 return sum(map(int,grouped)) if grouped else None


def coverage()->int|None:
 p=ROOT/'reports/LATEST_COVERAGE.txt'
 if not p.exists(): return None
 ms=re.findall(r'^TOTAL\s+\d+\s+\d+\s+(\d+)%',p.read_text(encoding='utf-8',errors='ignore'),re.M)
 return int(ms[-1]) if ms else None

def build()->dict:
 doc=yaml.safe_load(MATRIX.read_text(encoding='utf-8')); rows=doc['requirements']
 allc=Counter(r.get('status','MISSING') for r in rows)
 p0=[r for r in rows if r.get('priority')=='P0']; p0c=Counter(r.get('status','MISSING') for r in p0)
 manifest=json.loads(MANIFEST.read_text(encoding='utf-8')) if MANIFEST.exists() else {}
 test_evidence=manifest.get('test_evidence',{}) if isinstance(manifest.get('test_evidence',{}),dict) else {}
 acceptance=manifest.get('acceptance',{})
 blockers=[]
 if any(r.get('status')!='PASS' for r in p0): blockers.append(f"P0 requirements not all PASS ({dict(p0c)})")
 for k in REQUIRED_EXTERNAL_ACCEPTANCE:
  v=acceptance.get(k,'MISSING')
  if v!='PASS':
   blockers.append(f'{k}={v}')
 source_locks=verify_source_locks(ROOT)
 for problem in source_locks['problems']:
  blockers.append('source lock non-compliant: '+problem)
 return {
  'schema_version':'1.0','generated_at':datetime.now(timezone.utc).isoformat(),
  'release_id':manifest.get('release_id','UNKNOWN'),'release_classification':manifest.get('release_classification','UNKNOWN'),
  'prod_live_status':manifest.get('prod_live_status','BLOCKED'),'live_enabled':manifest.get('live_enabled',False),'default_mode':manifest.get('default_mode','PAPER'),
  'test_count':test_evidence.get('test_count',test_count()),
  'backend_coverage_percent':test_evidence.get('coverage_percent'),
  'coverage_fresh':test_evidence.get('coverage_fresh',False),
  'coverage_classification':test_evidence.get('coverage_classification','UNKNOWN'),
  'source_lock_compliance':source_locks,
  'requirements':{'total':len(rows),'counts':dict(allc),'p0_total':len(p0),'p0_counts':dict(p0c)},
  'matrix_sha256':sha256(MATRIX),'manifest_sha256':sha256(MANIFEST) if MANIFEST.exists() else None,
  'blockers':blockers,
 }

def render(s:dict)->str:
 c=s['requirements']['counts']; p=s['requirements']['p0_counts']
 lines=[
 '# Known Issues / Limitations','',
 f"Release: `{s['release_id']}`",'',
 f"Release classification: `{s['release_classification']}`. PROD LIVE: **{s['prod_live_status']}**; default mode: **{s['default_mode']}**; live_enabled: **{s['live_enabled']}**.",'',
 f"Current evidence snapshot: **{s['test_count']} tests collected**, backend coverage **{s['backend_coverage_percent']}** (fresh={s['coverage_fresh']}, classification={s['coverage_classification']}). Requirements: **{s['requirements']['total']} total / {c.get('PASS',0)} PASS / {c.get('NOT_TESTED',0)} NOT_TESTED / {c.get('UNSUPPORTED',0)} UNSUPPORTED**. P0: **{s['requirements']['p0_total']} total / {p.get('PASS',0)} PASS / {p.get('NOT_TESTED',0)} NOT_TESTED**.",'',
 '## Current production blockers',''
 ]
 for i,b in enumerate(s['blockers'],1): lines.append(f'{i}. {b}')
 lines += ['', 'This file is generated from the acceptance matrix and release manifest; edit the source evidence/status, not these counts manually.', '']
 return '\n'.join(lines)

def main()->None:
 s=build(); OUT_JSON.write_text(json.dumps(s,ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf-8'); OUT_MD.write_text(render(s),encoding='utf-8')
 print(json.dumps({'test_count':s['test_count'],'coverage':s['backend_coverage_percent'],'p0':s['requirements']['p0_counts'],'blockers':len(s['blockers'])},ensure_ascii=False))
if __name__=='__main__': main()
