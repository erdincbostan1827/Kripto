from __future__ import annotations

import argparse
import hashlib
import json
import re
import stat
import subprocess
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUT = ROOT / "reports" / "PHASE177_EXTERNAL_ACCEPTANCE_HANDOFF.zip"
MANIFEST_NAME = "HANDOFF_MANIFEST.json"
CLASSIFICATION = "EXTERNAL_ACCEPTANCE_HANDOFF_NOT_ACCEPTANCE_EVIDENCE"

# Deliberately excludes .env files, runtime logs, credentials, and generated
# external acceptance manifests. The bundle is a contract/runbook snapshot,
# not acceptance evidence and not a secret transport mechanism.
FILES = (
    "ACCEPTANCE_CLOSURE_RUNBOOK.md",
    "RELEASE_MANIFEST.json",
    "REQUIREMENTS_TRACEABILITY_MATRIX.yaml",
    "reports/ACCEPTANCE_CLOSURE_STATUS.json",
    "reports/PHASE176_READINESS.json",
    "reports/PHASE177_ACCEPTANCE_CAPABILITIES.json",
    "reports/PRODUCTION_READINESS_DOSSIER.json",
    "scripts/acceptance_diagnostics.py",
    "scripts/external_acceptance_preflight.py",
    "scripts/external_acceptance_runner.py",
    "scripts/generate_acceptance_challenge.py",
    "scripts/merge_external_acceptance.py",
    "scripts/lock_promotion_manifest.py",
    "scripts/verify_external_acceptance.py",
    "scripts/external/run_all_external_requirements.py",
    "scripts/external/acceptance_return_bundle.py",
    "scripts/external/acceptance_return_promotion.py",
    "scripts/external/binance_testnet_acceptance.py",
    "scripts/external/campaign_evidence_acceptance.py",
    "scripts/external/frontend_browser_acceptance.py",
    "scripts/external/generate_campaign_evidence_templates.py",
    "scripts/external/generate_dependency_license_report.py",
    "scripts/external/ha_failover_drill.sh",
    "scripts/external/ledger_checkpoint_sign_verify.sh",
    "scripts/external/pitr_restore_drill.sh",
    "scripts/external/provenance_capture.py",
    "scripts/external/provenance_sign_verify.sh",
    "scripts/external/runtime_restart_drill.sh",
    "scripts/external/tauri_build_readiness.py",
    "scripts/external/toolchain_readiness.py",
    "scripts/external/verify_drill_evidence.py",
    "scripts/external/verify_ledger_checkpoint.py",
    "scripts/external/verify_provenance_signature.py",
    "scripts/external/verify_restart_evidence.py",
    "scripts/external/verify_scanner_image_digests.py",
    "scripts/external/verify_supply_chain_artifacts.py",
    "scripts/external/verify_transferred_supply_chain.py",
    "scripts/external/worm_storage_acceptance.sh",
    "backend/app/release/acceptance_challenge.py",
    "backend/app/release/acceptance_contract.py",
    "backend/app/release/evidence_ledger.py",
)

# Conservative secret/value patterns. Environment variable *names* are allowed;
# assignments containing values are not.
_SECRET_PATTERNS = (
    re.compile(rb"(?i)(api[_-]?key|api[_-]?secret|access[_-]?token|refresh[_-]?token|password|passwd)\s*[:=]\s*['\"]?[^\s'\";,}]{8,}"),
    re.compile(rb"(?i)authorization\s*:\s*(bearer|basic)\s+[A-Za-z0-9._~+/=-]{8,}"),
    re.compile(rb"(?i)https?://[^\s/:]+:[^\s/@]+@"),
)


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _git_sha(root: Path) -> str | None:
    try:
        value = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return None
    return value if len(value) == 40 else None


def _source_identity(root: Path) -> dict:
    git = _git_sha(root)
    if git:
        return {"identity_mode": "GIT_HEAD", "git_commit_sha": git}
    package_manifest = root / "PACKAGE_MANIFEST.json"
    if package_manifest.is_file():
        try:
            payload = json.loads(package_manifest.read_text(encoding="utf-8"))
        except Exception:
            payload = {}
        digest = payload.get("content_set_sha256")
        if isinstance(digest, str) and len(digest) == 64:
            return {"identity_mode": "PACKAGE_CONTENT_SET", "content_set_sha256": digest}
    return {"identity_mode": "UNBOUND"}


def _zip_info(name: str, executable: bool = False) -> zipfile.ZipInfo:
    info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
    info.compress_type = zipfile.ZIP_DEFLATED
    info.create_system = 3
    info.external_attr = (stat.S_IFREG | (0o755 if executable else 0o644)) << 16
    return info


def _secret_hits(data: bytes) -> list[str]:
    return [f"SECRET_PATTERN:{i}" for i, pattern in enumerate(_SECRET_PATTERNS, start=1) if pattern.search(data)]


def build(root: Path = ROOT, out: Path = DEFAULT_OUT) -> dict:
    root = root.resolve()
    entries: list[dict] = []
    missing: list[str] = []
    for rel in FILES:
        path = root / rel
        if not path.is_file():
            missing.append(rel)
            continue
        if path.is_symlink():
            raise ValueError(f"HANDOFF_SYMLINK_NOT_ALLOWED:{rel}")
        data = path.read_bytes()
        hits = _secret_hits(data)
        if hits:
            raise ValueError(f"HANDOFF_SECRET_PATTERN:{rel}:{','.join(hits)}")
        entries.append({
            "path": rel,
            "sha256": _sha(data),
            "size": len(data),
            "executable": bool(path.stat().st_mode & stat.S_IXUSR),
        })
    if missing:
        raise FileNotFoundError("HANDOFF_REQUIRED_FILES_MISSING:" + ",".join(sorted(missing)))

    manifest = {
        "schema_version": "1.0",
        "classification": CLASSIFICATION,
        "truth_policy": "This bundle transfers acceptance contracts and runbooks only. It can never promote a requirement, profile, or release gate to PASS.",
        "source_identity": _source_identity(root),
        "file_count": len(entries),
        "files": entries,
        "secret_transport": False,
        "required_operator_action": "Run the canonical commands on the real isolated acceptance host, then transfer only checksum-bound evidence through the repository verifier/merge path.",
    }
    if manifest["source_identity"]["identity_mode"] == "UNBOUND":
        raise ValueError("HANDOFF_SOURCE_IDENTITY_UNBOUND")

    manifest_bytes = (json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.unlink(missing_ok=True)
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for row in entries:
            p = root / row["path"]
            zf.writestr(_zip_info(row["path"], row["executable"]), p.read_bytes())
        zf.writestr(_zip_info(MANIFEST_NAME), manifest_bytes)
    return {"archive": str(out), "sha256": _sha(out.read_bytes()), "manifest": manifest}


def verify(path: Path) -> dict:
    problems: list[str] = []
    try:
        with zipfile.ZipFile(path, "r") as zf:
            infos = zf.infolist()
            names = [i.filename for i in infos]
            if len(names) != len(set(names)):
                problems.append("DUPLICATE_MEMBER")
            for info in infos:
                name = info.filename
                parts = Path(name).parts
                if name.startswith("/") or ".." in parts or "\\" in name or "\x00" in name:
                    problems.append(f"UNSAFE_MEMBER:{name}")
                unix_type = (info.external_attr >> 16) & 0o170000
                if info.create_system == 3 and unix_type not in {0, stat.S_IFREG}:
                    problems.append(f"SPECIAL_MEMBER:{name}")
            if MANIFEST_NAME not in names:
                return {"verified": False, "problems": sorted(set(problems + ["MANIFEST_MISSING"]))}
            manifest = json.loads(zf.read(MANIFEST_NAME))
            if manifest.get("schema_version") != "1.0":
                problems.append("MANIFEST_SCHEMA_INVALID")
            if manifest.get("classification") != CLASSIFICATION:
                problems.append("MANIFEST_CLASSIFICATION_INVALID")
            if manifest.get("secret_transport") is not False:
                problems.append("SECRET_TRANSPORT_POLICY_INVALID")
            source_identity = manifest.get("source_identity") or {}
            if source_identity.get("identity_mode") not in {"GIT_HEAD", "PACKAGE_CONTENT_SET"}:
                problems.append("SOURCE_IDENTITY_UNBOUND")
            rows = manifest.get("files") if isinstance(manifest.get("files"), list) else []
            if manifest.get("file_count") != len(rows):
                problems.append("FILE_COUNT_MISMATCH")
            expected = {MANIFEST_NAME}
            seen: set[str] = set()
            for row in rows:
                if not isinstance(row, dict) or not isinstance(row.get("path"), str):
                    problems.append("MANIFEST_ENTRY_INVALID")
                    continue
                name = row["path"]
                if name in seen:
                    problems.append(f"MANIFEST_DUPLICATE:{name}")
                seen.add(name); expected.add(name)
                if name not in names:
                    problems.append(f"MEMBER_MISSING:{name}")
                    continue
                data = zf.read(name)
                if _sha(data) != row.get("sha256"):
                    problems.append(f"HASH_MISMATCH:{name}")
                if len(data) != row.get("size"):
                    problems.append(f"SIZE_MISMATCH:{name}")
                problems.extend(f"{hit}:{name}" for hit in _secret_hits(data))
            unexpected = set(names) - expected
            if unexpected:
                problems.extend(f"UNEXPECTED_MEMBER:{name}" for name in sorted(unexpected))
    except Exception as exc:
        problems.append(f"ARCHIVE_INVALID:{type(exc).__name__}")
    return {"verified": not problems, "problems": sorted(set(problems))}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--verify", type=Path)
    args = parser.parse_args()
    if args.verify:
        result = verify(args.verify)
    else:
        result = build(out=args.output)
        result["verification"] = verify(Path(result["archive"]))
    print(json.dumps(result, indent=2, sort_keys=True))
    verified = result.get("verified", result.get("verification", {}).get("verified", False))
    return 0 if verified else 2


if __name__ == "__main__":
    raise SystemExit(main())
