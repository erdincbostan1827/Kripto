from __future__ import annotations

import hashlib
import json
import stat
import subprocess
import zipfile
from pathlib import Path

try:
    from scripts.package_evidence import build_evidence_archive, verify_evidence_archive
    from scripts.package_release import build_release, verify_archive, scan_zip_safety
    from scripts.verify_release_consistency import verify as verify_release_consistency
except ModuleNotFoundError:  # direct `python scripts/package_distribution.py` execution
    from package_evidence import build_evidence_archive, verify_evidence_archive
    from package_release import build_release, verify_archive, scan_zip_safety
    from verify_release_consistency import verify as verify_release_consistency

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT.parent
DISTRIBUTION = OUT_DIR / "crypto_trading_platform_v5_1_distribution-local.zip"
BUNDLE_MANIFEST = "RELEASE_BUNDLE.json"
PACKAGE_PROVENANCE = OUT_DIR / "PACKAGE_PROVENANCE.json"


def sha256_file(path: Path) -> str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):
            h.update(chunk)
    return h.hexdigest()


def git_sha(root: Path=ROOT) -> str:
    try:
        return subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True,stderr=subprocess.DEVNULL).strip()
    except Exception:
        return 'UNAVAILABLE'


def _json(path: Path) -> dict:
    try: return json.loads(path.read_text(encoding='utf-8'))
    except Exception: return {}


def validate_release_binding(root: Path=ROOT, expected_git_sha: str|None=None) -> dict:
    sha=expected_git_sha or git_sha(root)
    release=_json(root/'RELEASE_MANIFEST.json')
    provenance=_json(root/'reports/LOCAL_SOURCE_PROVENANCE.json')
    problems=[]
    if sha=='UNAVAILABLE': problems.append('GIT_SHA_UNAVAILABLE')
    if release.get('git_commit_sha')!=sha: problems.append('RELEASE_MANIFEST_GIT_MISMATCH')
    if provenance.get('git_commit_sha')!=sha: problems.append('SOURCE_PROVENANCE_GIT_MISMATCH')
    if provenance.get('clean_tree') is not True: problems.append('SOURCE_PROVENANCE_NOT_CLEAN')
    if provenance.get('immutable_tag_present') is not True: problems.append('IMMUTABLE_TAG_MISSING')
    if release.get('default_mode')!='PAPER': problems.append('DEFAULT_MODE_NOT_PAPER')
    if release.get('live_enabled') is not False: problems.append('LIVE_NOT_DISABLED')
    consistency = verify_release_consistency(root)
    if not consistency.get('verified'):
        problems.extend('RELEASE_CONSISTENCY:'+x for x in consistency.get('problems',[]))
    return {'verified':not problems,'git_commit_sha':sha,'problems':problems,'release':release}


def _zi(name:str)->zipfile.ZipInfo:
    i=zipfile.ZipInfo(name,date_time=(1980,1,1,0,0,0)); i.compress_type=zipfile.ZIP_DEFLATED
    i.external_attr=(stat.S_IFREG|0o644)<<16; i.create_system=3; return i


def build_distribution(root: Path=ROOT, archive: Path=DISTRIBUTION) -> tuple[Path,dict]:
    binding=validate_release_binding(root)
    if not binding['verified']:
        raise RuntimeError('release binding verification failed: '+','.join(binding['problems']))
    source_archive,_=build_release(root=root,archive=OUT_DIR/'crypto_trading_platform_v5_1_0.3.0-local-acceptance.zip')
    if verify_archive(source_archive)!={'forbidden':[],'mismatches':[]}:
        raise RuntimeError('source archive verification failed')
    evidence_archive,evidence_manifest=build_evidence_archive(root=root,archive=OUT_DIR/'crypto_trading_platform_v5_1_evidence-local.zip')
    ev=verify_evidence_archive(evidence_archive)
    if not ev['verified']: raise RuntimeError('evidence archive verification failed')
    if evidence_manifest.get('git_commit_sha')!=binding['git_commit_sha']:
        raise RuntimeError('evidence archive git binding mismatch')
    release=binding['release']
    manifest={
      'schema_version':'1.0',
      'classification':'LOCAL_ACCEPTANCE_DISTRIBUTION_NOT_PRODUCTION_READY' if release.get('prod_live_status')!='READY' else 'PRODUCTION_ACCEPTANCE_DISTRIBUTION',
      'git_commit_sha':binding['git_commit_sha'],
      'prod_live_status':release.get('prod_live_status','BLOCKED'),
      'default_mode':release.get('default_mode'),
      'live_enabled':release.get('live_enabled'),
      'truth_policy':'This bundle transports source and evidence. It never promotes LIVE status beyond RELEASE_MANIFEST.json.',
      'artifacts':[
        {'role':'source','name':source_archive.name,'sha256':sha256_file(source_archive),'size':source_archive.stat().st_size},
        {'role':'evidence','name':evidence_archive.name,'sha256':sha256_file(evidence_archive),'size':evidence_archive.stat().st_size},
      ],
    }
    mb=(json.dumps(manifest,ensure_ascii=False,indent=2,sort_keys=True)+'\n').encode()
    checks=''.join(f"{a['sha256']}  {a['name']}\n" for a in manifest['artifacts']).encode()
    archive.unlink(missing_ok=True)
    with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        z.writestr(_zi(source_archive.name),source_archive.read_bytes())
        z.writestr(_zi(evidence_archive.name),evidence_archive.read_bytes())
        z.writestr(_zi(BUNDLE_MANIFEST),mb)
        z.writestr(_zi('SHA256SUMS.txt'),checks)
    return archive,manifest


def verify_distribution(archive: Path=DISTRIBUTION)->dict:
    problems=[]
    with zipfile.ZipFile(archive) as z:
        problems.extend('ARCHIVE_SAFETY:'+p for p in scan_zip_safety(z))
        raw_names=z.namelist()
        if len(raw_names)!=len(set(raw_names)):
            problems.append('DUPLICATE_ARCHIVE_MEMBER')
        names=set(raw_names)
        if BUNDLE_MANIFEST not in names:
            return {'verified':False,'problems':sorted(set(problems+['BUNDLE_MANIFEST_MISSING']))}
        try:
            m=json.loads(z.read(BUNDLE_MANIFEST))
        except Exception as exc:
            return {'verified':False,'problems':sorted(set(problems+[f'BUNDLE_MANIFEST_INVALID:{type(exc).__name__}']))}
        if m.get('schema_version')!='1.0': problems.append('BUNDLE_SCHEMA_INVALID')
        artifacts=m.get('artifacts') if isinstance(m.get('artifacts'),list) else []
        expected_names={BUNDLE_MANIFEST,'SHA256SUMS.txt'}
        checksum_lines=[]
        for a in artifacts:
            if not isinstance(a,dict):
                problems.append('ARTIFACT_ENTRY_INVALID'); continue
            name=a.get('name')
            if not isinstance(name,str) or Path(name).is_absolute() or '..' in Path(name).parts or '/' in name or '\\' in name:
                problems.append('ARTIFACT_NAME_INVALID:'+str(name)); continue
            expected_names.add(name)
            if name not in names: problems.append('ARTIFACT_MISSING:'+name); continue
            data=z.read(name)
            if hashlib.sha256(data).hexdigest()!=a.get('sha256'): problems.append('ARTIFACT_HASH_MISMATCH:'+name)
            if len(data)!=a.get('size'): problems.append('ARTIFACT_SIZE_MISMATCH:'+name)
            checksum_lines.append(f"{a.get('sha256')}  {name}\n")
        for extra in sorted(names-expected_names):
            problems.append('UNEXPECTED_MEMBER:'+extra)
        if 'SHA256SUMS.txt' not in names:
            problems.append('SHA256SUMS_MISSING')
        elif z.read('SHA256SUMS.txt') != ''.join(checksum_lines).encode():
            problems.append('SHA256SUMS_MISMATCH')
        if m.get('live_enabled') is not False: problems.append('LIVE_NOT_DISABLED')
        if m.get('default_mode')!='PAPER': problems.append('DEFAULT_MODE_NOT_PAPER')
    return {'verified':not problems,'problems':sorted(set(problems))}



def build_package_provenance(*, root: Path, distribution: Path, bundle_manifest: dict, output: Path = PACKAGE_PROVENANCE) -> dict:
    release_path = root / "RELEASE_MANIFEST.json"
    release = _json(release_path)
    artifact_map = {row.get("role"): row for row in bundle_manifest.get("artifacts", []) if isinstance(row, dict)}
    payload = {
        "schema_version": "1.0",
        "classification": "LOCAL_PACKAGE_PROVENANCE_NOT_CI_PROVENANCE" if release.get("ci_run_id") in (None, "", "LOCAL-NOT-CI") else "CI_BOUND_PACKAGE_PROVENANCE",
        "git_commit_sha": bundle_manifest.get("git_commit_sha"),
        "distribution_archive": {
            "name": distribution.name,
            "sha256": sha256_file(distribution),
            "size": distribution.stat().st_size,
        },
        "source_archive": artifact_map.get("source"),
        "evidence_archive": artifact_map.get("evidence"),
        "release_manifest_sha256": sha256_file(release_path) if release_path.is_file() else None,
        "release_status": {
            "prod_live_status": release.get("prod_live_status", "BLOCKED"),
            "default_mode": release.get("default_mode"),
            "live_enabled": release.get("live_enabled"),
        },
        "build_provenance": {
            "ci_run_id": release.get("ci_run_id"),
            "dependency_lock_hash": release.get("dependency_lock_hash"),
            "frontend_lock_hash": release.get("frontend_lock_hash"),
            "sbom_hash": release.get("sbom_hash"),
            "license_report_hash": release.get("license_report_hash"),
            "supply_chain_verification_hash": release.get("supply_chain_verification_hash"),
            "scanner_image_digest_manifest_hash": release.get("scanner_image_digest_manifest_hash"),
            "frontend_artifact_hash": release.get("frontend_artifact_hash"),
            "container_digest": release.get("container_digest"),
            "source_tree_hash": release.get("source_tree_hash"),
        },
        "truth_policy": "This file binds the final distribution archive to source/evidence hashes and release metadata. LOCAL_PACKAGE_PROVENANCE_NOT_CI_PROVENANCE is not a substitute for signed CI provenance.",
    }
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def verify_package_provenance(path: Path = PACKAGE_PROVENANCE, *, root: Path = ROOT) -> dict:
    problems: list[str] = []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"verified": False, "problems": [f"INVALID_JSON:{type(exc).__name__}"]}
    archive_info = payload.get("distribution_archive") if isinstance(payload.get("distribution_archive"), dict) else {}
    archive = path.parent / str(archive_info.get("name", ""))
    if not archive.is_file():
        problems.append("DISTRIBUTION_ARCHIVE_MISSING")
    else:
        if sha256_file(archive) != archive_info.get("sha256"):
            problems.append("DISTRIBUTION_ARCHIVE_HASH_MISMATCH")
        if archive.stat().st_size != archive_info.get("size"):
            problems.append("DISTRIBUTION_ARCHIVE_SIZE_MISMATCH")
    release_path = root / "RELEASE_MANIFEST.json"
    if not release_path.is_file() or sha256_file(release_path) != payload.get("release_manifest_sha256"):
        problems.append("RELEASE_MANIFEST_HASH_MISMATCH")
    if archive.is_file():
        distribution_result = verify_distribution(archive)
        if not distribution_result.get("verified"):
            problems.extend(f"DISTRIBUTION_VERIFY:{x}" for x in distribution_result.get("problems", []))
        try:
            with zipfile.ZipFile(archive) as z:
                bundle = json.loads(z.read(BUNDLE_MANIFEST))
            by_role = {row.get("role"): row for row in bundle.get("artifacts", []) if isinstance(row, dict)}
            for role, field in (("source", "source_archive"), ("evidence", "evidence_archive")):
                if payload.get(field) != by_role.get(role):
                    problems.append(f"{role.upper()}_ARCHIVE_PROVENANCE_MISMATCH")
        except Exception:
            problems.append("DISTRIBUTION_BUNDLE_MANIFEST_INVALID")
    release = _json(release_path)
    if payload.get("git_commit_sha") != git_sha(root):
        problems.append("GIT_COMMIT_MISMATCH")
    status = payload.get("release_status") if isinstance(payload.get("release_status"), dict) else {}
    if status.get("default_mode") != "PAPER":
        problems.append("DEFAULT_MODE_NOT_PAPER")
    if status.get("live_enabled") is not False:
        problems.append("LIVE_NOT_DISABLED")
    if status.get("prod_live_status") != release.get("prod_live_status", "BLOCKED"):
        problems.append("RELEASE_STATUS_MISMATCH")
    return {"verified": not problems, "problems": sorted(problems), "classification": payload.get("classification")}

def main()->int:
    archive,m=build_distribution(); v=verify_distribution(archive)
    provenance = build_package_provenance(root=ROOT, distribution=archive, bundle_manifest=m)
    pv = verify_package_provenance(PACKAGE_PROVENANCE, root=ROOT)
    print(json.dumps({'archive':str(archive),'sha256':sha256_file(archive),'git_commit_sha':m['git_commit_sha'],'prod_live_status':m['prod_live_status'],'package_provenance':str(PACKAGE_PROVENANCE),'package_provenance_sha256':sha256_file(PACKAGE_PROVENANCE),'package_provenance_verified':pv['verified'],**v}))
    return 0 if v['verified'] and pv['verified'] else 1

if __name__=='__main__': raise SystemExit(main())
