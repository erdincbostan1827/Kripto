from __future__ import annotations

import argparse
import os
import shutil
import stat
import tempfile
import zipfile
from pathlib import Path, PurePosixPath

try:
    from scripts.package_release import scan_zip_safety, verify_archive
    from scripts.verify_source_package_identity import verify_source_package_identity
except ModuleNotFoundError:
    from package_release import scan_zip_safety, verify_archive
    from verify_source_package_identity import verify_source_package_identity


def _safe_target(root: Path, member: str) -> Path:
    posix = PurePosixPath(member)
    if posix.is_absolute() or ".." in posix.parts:
        raise ValueError(f"unsafe zip member: {member}")
    target = (root / Path(*posix.parts)).resolve()
    target.relative_to(root.resolve())
    return target


def extract(package: Path, destination: Path, *, verify_manifest_if_present: bool = True) -> dict:
    manifest_member: str | None = None
    with zipfile.ZipFile(package) as probe:
        safety_problems = scan_zip_safety(probe)
        if safety_problems:
            raise ValueError(f"unsafe source package: {safety_problems}")
        manifest_members = [name for name in probe.namelist() if name.endswith("/PACKAGE_MANIFEST.json")]
        has_manifest = bool(manifest_members)
        if len(manifest_members) > 1:
            raise ValueError("source package contains multiple package manifests")
        manifest_member = manifest_members[0] if manifest_members else None
    if verify_manifest_if_present and has_manifest:
        verification = verify_archive(package)
        if verification.get("forbidden") or verification.get("mismatches"):
            raise ValueError(f"source package integrity verification failed: {verification}")
    destination_preexisted = destination.exists()
    if destination_preexisted:
        if not destination.is_dir():
            raise ValueError("source package destination is not a directory")
        if any(destination.iterdir()):
            raise ValueError("source package destination must be empty")
    destination.parent.mkdir(parents=True, exist_ok=True)

    # Extract transactionally into a sibling staging directory.  This prevents a
    # corrupt/tampered archive, I/O failure, or post-extraction identity failure
    # from leaving a partially populated destination that could be mistaken for
    # a verified source tree.
    staging = Path(tempfile.mkdtemp(prefix=f".{destination.name}.extract-", dir=destination.parent))
    files = 0
    executable_files: list[str] = []
    extracted_identity_verified = False
    try:
        with zipfile.ZipFile(package) as zf:
            for info in zf.infolist():
                target = _safe_target(staging, info.filename)
                if info.is_dir():
                    target.mkdir(parents=True, exist_ok=True)
                    continue
                target.parent.mkdir(parents=True, exist_ok=True)
                with zf.open(info, "r") as src, target.open("wb") as dst:
                    shutil.copyfileobj(src, dst)
                unix_mode = (info.external_attr >> 16) & 0o7777
                if unix_mode:
                    os.chmod(target, unix_mode)
                if unix_mode & 0o111:
                    executable_files.append(info.filename)
                files += 1
        if verify_manifest_if_present and has_manifest and manifest_member:
            manifest_rel = PurePosixPath(manifest_member)
            extracted_root = staging / Path(*manifest_rel.parent.parts)
            identity = verify_source_package_identity(extracted_root)
            if not identity.get("verified"):
                raise ValueError(f"post-extraction source identity verification failed: {identity.get('problems')}")
            extracted_identity_verified = True

        if destination_preexisted:
            destination.rmdir()
        os.replace(staging, destination)
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        if destination_preexisted and not destination.exists():
            destination.mkdir(parents=False, exist_ok=False)
        raise
    return {
        "classification": "SOURCE_PACKAGE_SAFE_EXTRACTION",
        "manifest_verified": bool(verify_manifest_if_present and has_manifest),
        "extracted_identity_verified": extracted_identity_verified,
        "files_extracted": files,
        "executable_files_restored": sorted(executable_files),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("package", type=Path)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    result = extract(args.package.resolve(), args.destination.resolve())
    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
