from __future__ import annotations
import importlib.metadata as md
import json, re, sys, tomllib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'reports/external_acceptance/dependency_licenses.json'
PRE=ROOT/'reports/external_acceptance/dependency_licenses.preflight.json'

def _parse_req(raw:str):
    m=re.match(r'^([A-Za-z0-9_.-]+)(?:\[[^]]+\])?==(.+)$', raw)
    if not m: raise ValueError(raw)
    return m.group(1),m.group(2)

def build(root:Path=ROOT)->dict:
    problems=[]; rows=[]
    uv=root/'uv.lock'; npm_lock=root/'frontend/package-lock.json'
    if not uv.is_file(): problems.append('UV_LOCK_MISSING')
    if not npm_lock.is_file(): problems.append('FRONTEND_LOCK_MISSING')
    py=tomllib.loads((root/'pyproject.toml').read_text())
    pyreq=list(py['project'].get('dependencies',[]))+list(py['project'].get('optional-dependencies',{}).get('test',[]))+list(py.get('build-system',{}).get('requires',[]))
    for raw in pyreq:
        try: name,expected=_parse_req(raw)
        except ValueError:
            problems.append(f'PYTHON_REQUIREMENT_NOT_EXACT:{raw}'); continue
        try:
            actual=md.version(name); meta=md.metadata(name)
        except md.PackageNotFoundError:
            problems.append(f'PYTHON_PACKAGE_NOT_INSTALLED:{name}'); continue
        if actual!=expected: problems.append(f'PYTHON_VERSION_MISMATCH:{name}:{expected}:{actual}')
        lic=(meta.get('License-Expression') or meta.get('License') or '').strip()
        if not lic: problems.append(f'PYTHON_LICENSE_MISSING:{name}')
        rows.append({'Name':name,'Version':actual,'License':lic or 'UNRESOLVED','Ecosystem':'python','Source':'installed-metadata'})
    pkg=json.loads((root/'frontend/package.json').read_text())
    expected_js={**pkg.get('dependencies',{}),**pkg.get('devDependencies',{})}
    for name,expected in sorted(expected_js.items()):
        p=root/'frontend/node_modules'/name/'package.json'
        if not p.is_file(): problems.append(f'NPM_PACKAGE_NOT_INSTALLED:{name}'); continue
        try: item=json.loads(p.read_text())
        except Exception: problems.append(f'NPM_PACKAGE_METADATA_INVALID:{name}'); continue
        actual=str(item.get('version') or '')
        if actual!=expected: problems.append(f'NPM_VERSION_MISMATCH:{name}:{expected}:{actual}')
        lic=item.get('license')
        if isinstance(lic,dict): lic=lic.get('type')
        if not isinstance(lic,str) or not lic.strip(): problems.append(f'NPM_LICENSE_MISSING:{name}'); lic='UNRESOLVED'
        rows.append({'Name':name,'Version':actual,'License':lic,'Ecosystem':'npm','Source':'node_modules-package-json'})
    payload={'schema_version':'1.0','classification':'DEPENDENCY_LICENSE_REPORT_PREFLIGHT','verified':not problems,'problems':sorted(set(problems)),'packages':rows}
    PRE.parent.mkdir(parents=True,exist_ok=True); PRE.write_text(json.dumps(payload,indent=2,sort_keys=True)+'\n')
    if not problems:
        OUT.write_text(json.dumps(rows,indent=2,sort_keys=True)+'\n')
    elif OUT.exists(): OUT.unlink()
    return payload

def main():
    r=build(); print(json.dumps(r,indent=2,sort_keys=True)); return 0 if r['verified'] else 2
if __name__=='__main__': raise SystemExit(main())
