from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = "ACCEPTANCE_RETURN_MANIFEST.json"
CLASSIFICATION = "EXTERNAL_ACCEPTANCE_RETURN_TRANSPORT_NOT_ACCEPTANCE_BY_ITSELF"

# Only evidence/lock artifacts are eligible. Runtime env files, arbitrary logs,
# credentials and operator home files are never swept into a return bundle.
BASE_FILES = (
    "reports/CI_BUILD_EVIDENCE_MANIFEST.json",
    "reports/lock-promotion/LOCK_PROMOTION_MANIFEST.json",
    "reports/external_acceptance/release_challenge.json",
    "reports/external_acceptance/evidence_ledger.json",
    "reports/external_acceptance/ledger_checkpoint.json",
    "reports/external_acceptance/ledger_checkpoint.sig",
    "reports/external_acceptance/manifest_all.json",
    "reports/external_acceptance/sbom.cdx.json",
    "reports/external_acceptance/dependency_licenses.json",
    "reports/external_acceptance/supply_chain_artifact_verification.json",
    "reports/external_acceptance/scanner_image_digests.json",
    "reports/external_acceptance/provenance.json",
    "uv.lock",
    "frontend/package-lock.json",
)
_PROFILE_NAMES = ("runtime", "testnet", "market", "recovery", "supply_chain", "frontend")
_SECRET_PATTERNS = (
    re.compile(rb"(?i)(api[_-]?key|api[_-]?secret|access[_-]?token|refresh[_-]?token|password|passwd)\s*[:=]\s*['\"]?[^\s'\";,}]{8,}"),
    re.compile(rb"(?i)authorization\s*:\s*(bearer|basic)\s+[A-Za-z0-9._~+/=-]{8,}"),
    re.compile(rb"(?i)https?://[^\s/:]+:[^\s/@]+@"),
)


def _sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha(path: Path) -> str:
    return _sha_bytes(path.read_bytes())


def _git_sha(root: Path) -> str | None:
    try:
        value = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return None
    return value if len(value) == 40 else None


def _safe_rel(value: str) -> bool:
    p = Path(value)
    return bool(p.parts) and not p.is_absolute() and ".." not in p.parts and "\\" not in value and "\x00" not in value


def _secret_hits(data: bytes) -> list[str]:
    return [f"SECRET_PATTERN:{idx}" for idx, pat in enumerate(_SECRET_PATTERNS, 1) if pat.search(data)]


def _zip_info(name: str) -> zipfile.ZipInfo:
    info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
    info.compress_type = zipfile.ZIP_DEFLATED
    info.create_system = 3
    info.external_attr = (stat.S_IFREG | 0o644) << 16
    return info


def _referenced_evidence(root: Path) -> set[str]:
    refs: set[str] = set()
    reports = root / "reports" / "external_acceptance"
    for name in (*_PROFILE_NAMES, "all"):
        manifest = reports / f"manifest_{name}.json"
        if not manifest.is_file():
            continue
        try:
            doc = json.loads(manifest.read_text(encoding="utf-8"))
        except Exception:
            continue
        refs.add(manifest.relative_to(root).as_posix())
        for row in doc.get("evidence", []) or []:
            if not isinstance(row, dict):
                continue
            artifact = row.get("artifact")
            if isinstance(artifact, str) and artifact.startswith("reports/external_acceptance/") and _safe_rel(artifact):
                refs.add(artifact)
        sources = doc.get("source_profiles") or {}
        if isinstance(sources, dict):
            for row in sources.values():
                ref = row.get("reference") if isinstance(row, dict) else None
                if isinstance(ref, str) and ref.startswith("reports/external_acceptance/") and _safe_rel(ref):
                    refs.add(ref)
    return refs


def collect(root: Path = ROOT) -> list[str]:
    candidates = set(BASE_FILES) | _referenced_evidence(root)
    files: list[str] = []
    resolved_root = root.resolve()
    for rel in sorted(candidates):
        if not _safe_rel(rel):
            raise ValueError(f"RETURN_REFERENCE_UNSAFE:{rel}")
        raw = root / rel
        current = root
        for part in Path(rel).parts:
            current = current / part
            if current.is_symlink():
                raise ValueError(f"RETURN_SYMLINK_NOT_ALLOWED:{rel}")
        if not raw.is_file():
            continue
        resolved = raw.resolve()
        resolved.relative_to(resolved_root)
        data = resolved.read_bytes()
        hits = _secret_hits(data)
        if hits:
            raise ValueError(f"RETURN_SECRET_PATTERN:{rel}:{','.join(hits)}")
        files.append(rel)
    return files


def build(root: Path = ROOT, out: Path | None = None) -> dict:
    root = root.resolve()
    git_sha = _git_sha(root)
    if not git_sha:
        raise ValueError("RETURN_SOURCE_GIT_UNAVAILABLE")
    if out is None:
        out = root / "reports" / "EXTERNAL_ACCEPTANCE_RETURN.zip"
    rows = []
    for rel in collect(root):
        p = root / rel
        rows.append({"path": rel, "sha256": _sha(p), "size": p.stat().st_size})
    manifest = {
        "schema_version": "1.0",
        "classification": CLASSIFICATION,
        "truth_policy": "Transport verification never promotes acceptance. Canonical semantic verifiers and merge gates remain authoritative.",
        "source_git_commit_sha": git_sha,
        "file_count": len(rows),
        "files": rows,
        "secret_transport": False,
    }
    payload = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.unlink(missing_ok=True)
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for row in rows:
            zf.writestr(_zip_info(row["path"]), (root / row["path"]).read_bytes())
        zf.writestr(_zip_info(MANIFEST), payload)
    verification = verify(out, expected_git_sha=git_sha)
    return {"archive": str(out), "sha256": _sha(out), "manifest": manifest, "verification": verification}


def verify(archive: Path, *, expected_git_sha: str | None = None) -> dict:
    problems: list[str] = []
    manifest: dict = {}
    try:
        with zipfile.ZipFile(archive, "r") as zf:
            infos = zf.infolist()
            names = [i.filename for i in infos]
            if len(names) != len(set(names)):
                problems.append("DUPLICATE_MEMBER")
            for info in infos:
                name = info.filename
                if not _safe_rel(name):
                    problems.append(f"UNSAFE_MEMBER:{name}")
                unix_type = (info.external_attr >> 16) & 0o170000
                if info.create_system == 3 and unix_type not in {0, stat.S_IFREG}:
                    problems.append(f"SPECIAL_MEMBER:{name}")
            if MANIFEST not in names:
                return {"verified": False, "problems": sorted(set(problems + ["MANIFEST_MISSING"]))}
            manifest = json.loads(zf.read(MANIFEST))
            if manifest.get("schema_version") != "1.0": problems.append("MANIFEST_SCHEMA_INVALID")
            if manifest.get("classification") != CLASSIFICATION: problems.append("MANIFEST_CLASSIFICATION_INVALID")
            if manifest.get("secret_transport") is not False: problems.append("SECRET_TRANSPORT_POLICY_INVALID")
            source_git = manifest.get("source_git_commit_sha")
            if not isinstance(source_git, str) or len(source_git) != 40: problems.append("SOURCE_GIT_INVALID")
            if expected_git_sha and source_git != expected_git_sha: problems.append("SOURCE_GIT_MISMATCH")
            rows = manifest.get("files") if isinstance(manifest.get("files"), list) else []
            if manifest.get("file_count") != len(rows): problems.append("FILE_COUNT_MISMATCH")
            expected = {MANIFEST}; seen: set[str] = set()
            for row in rows:
                if not isinstance(row, dict) or not isinstance(row.get("path"), str):
                    problems.append("MANIFEST_ENTRY_INVALID"); continue
                name = row["path"]
                if not _safe_rel(name): problems.append(f"MANIFEST_PATH_UNSAFE:{name}"); continue
                if name in seen: problems.append(f"MANIFEST_DUPLICATE:{name}")
                seen.add(name); expected.add(name)
                if name not in names: problems.append(f"MEMBER_MISSING:{name}"); continue
                data = zf.read(name)
                if _sha_bytes(data) != row.get("sha256"): problems.append(f"HASH_MISMATCH:{name}")
                if len(data) != row.get("size"): problems.append(f"SIZE_MISMATCH:{name}")
                problems.extend(f"{hit}:{name}" for hit in _secret_hits(data))
            for name in sorted(set(names) - expected): problems.append(f"UNEXPECTED_MEMBER:{name}")
    except Exception as exc:
        problems.append(f"ARCHIVE_INVALID:{type(exc).__name__}")
    return {"verified": not problems, "problems": sorted(set(problems)), "source_git_commit_sha": manifest.get("source_git_commit_sha")}


def stage(archive: Path, *, root: Path = ROOT, staging_root: Path | None = None) -> dict:
    expected_git = _git_sha(root)
    if not expected_git:
        return {"staged": False, "problems": ["LOCAL_GIT_UNAVAILABLE"]}
    validation = verify(archive, expected_git_sha=expected_git)
    if not validation["verified"]:
        return {"staged": False, "problems": validation["problems"]}
    digest = _sha(archive)
    base = staging_root or (root / "reports" / "external_acceptance" / "incoming")
    target = base / digest
    if target.exists():
        marker = target / MANIFEST
        if marker.is_file():
            return {"staged": True, "idempotent": True, "path": str(target), "bundle_sha256": digest, "problems": []}
        return {"staged": False, "problems": ["STAGING_TARGET_COLLISION"]}
    base.mkdir(parents=True, exist_ok=True)
    temp = Path(tempfile.mkdtemp(prefix=f".{digest[:12]}-", dir=base))
    try:
        with zipfile.ZipFile(archive, "r") as zf:
            manifest = json.loads(zf.read(MANIFEST))
            for row in manifest["files"]:
                rel = row["path"]
                dest = temp / rel
                dest.parent.mkdir(parents=True, exist_ok=True)
                data = zf.read(rel)
                dest.write_bytes(data)
                os.chmod(dest, 0o600)
            (temp / MANIFEST).write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        os.replace(temp, target)
    except Exception:
        shutil.rmtree(temp, ignore_errors=True)
        raise
    return {"staged": True, "idempotent": False, "path": str(target), "bundle_sha256": digest, "problems": []}


def main() -> int:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="command", required=True)
    b = sub.add_parser("build"); b.add_argument("--output", type=Path)
    v = sub.add_parser("verify"); v.add_argument("archive", type=Path); v.add_argument("--expected-git-sha")
    s = sub.add_parser("stage"); s.add_argument("archive", type=Path); s.add_argument("--staging-root", type=Path)
    args = p.parse_args()
    if args.command == "build": result = build(out=args.output)
    elif args.command == "verify": result = verify(args.archive, expected_git_sha=args.expected_git_sha)
    else: result = stage(args.archive, staging_root=args.staging_root)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get("verification", result).get("verified", result.get("staged", False)) else 2


if __name__ == "__main__":
    raise SystemExit(main())
