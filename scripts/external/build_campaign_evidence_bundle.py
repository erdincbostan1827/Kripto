from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
import uuid
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
MANIFEST_NAME = "CAMPAIGN_BUNDLE_MANIFEST.json"
BUNDLE_CLASSIFICATION = "PHASE246_CAMPAIGN_EVIDENCE_TRANSFER_BUNDLE"
RECEIPT_CLASSIFICATION = "PHASE252_CAMPAIGN_BUNDLE_BUILD_RECEIPT"
GIT_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
REQUIRED_RECEIPTS = {
    "reports/external_acceptance/campaign/private_stream.json": "CREDENTIALED_PRIVATE_STREAM_ACCEPTANCE",
    "reports/external_acceptance/campaign/paper_campaign.json": "REAL_MARKET_PAPER_CAMPAIGN_ACCEPTANCE",
    "reports/external_acceptance/campaign/live_shadow.json": "LIVE_SHADOW_CAMPAIGN_ACCEPTANCE",
    "reports/external_acceptance/campaign/profitability.json": "REAL_PIT_PROFITABILITY_ACCEPTANCE",
}
CHALLENGE_PATH = "reports/external_acceptance/release_challenge.json"


def _sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_git_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8").strip()
    except (OSError, UnicodeError):
        return ""


def _resolve_git_dirs(root: Path) -> tuple[Path | None, Path | None]:
    marker = root / ".git"
    if marker.is_dir():
        git_dir = marker.resolve()
    elif marker.is_file():
        marker_text = _read_git_text(marker)
        prefix = "gitdir: "
        if not marker_text.lower().startswith(prefix):
            return None, None
        gitdir_value = marker_text[len(prefix) :].strip()
        if not gitdir_value:
            return None, None
        git_dir = (marker.parent / gitdir_value).resolve()
    else:
        return None, None

    common_dir = git_dir
    commondir_text = _read_git_text(git_dir / "commondir")
    if commondir_text:
        common_dir = (git_dir / commondir_text).resolve()
    return git_dir, common_dir


def _safe_git_ref(value: str) -> str | None:
    if not value.startswith("refs/") or "\\" in value or "\x00" in value:
        return None
    pure = PurePosixPath(value)
    if any(part in {"", ".", ".."} for part in pure.parts):
        return None
    return pure.as_posix()


def _loose_ref_sha(base: Path, ref_name: str) -> str | None:
    target = base.joinpath(*PurePosixPath(ref_name).parts)
    value = _read_git_text(target).lower()
    return value if GIT_SHA_RE.fullmatch(value) else None


def _packed_ref_sha(path: Path, ref_name: str) -> str | None:
    text = _read_git_text(path)
    if not text:
        return None
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or stripped.startswith("^"):
            continue
        fields = stripped.split(" ", 1)
        if len(fields) != 2 or fields[1] != ref_name:
            continue
        value = fields[0].lower()
        return value if GIT_SHA_RE.fullmatch(value) else None
    return None


def _git_sha(root: Path) -> str:
    git_dir, common_dir = _resolve_git_dirs(root)
    if git_dir is None or common_dir is None:
        return "UNAVAILABLE"

    head = _read_git_text(git_dir / "HEAD")
    detached = head.lower()
    if GIT_SHA_RE.fullmatch(detached):
        return detached
    if not head.startswith("ref: "):
        return "UNAVAILABLE"

    ref_name = _safe_git_ref(head[5:].strip())
    if ref_name is None:
        return "UNAVAILABLE"

    ref_dirs = (git_dir, common_dir) if git_dir != common_dir else (git_dir,)
    for base in ref_dirs:
        loose = _loose_ref_sha(base, ref_name)
        if loose is not None:
            return loose

    packed_paths = (git_dir / "packed-refs", common_dir / "packed-refs")
    seen: set[Path] = set()
    for packed_path in packed_paths:
        if packed_path in seen:
            continue
        seen.add(packed_path)
        packed = _packed_ref_sha(packed_path, ref_name)
        if packed is not None:
            return packed
    return "UNAVAILABLE"


def _safe_rel(value: str) -> str:
    if "\\" in value or "\x00" in value:
        raise ValueError("SOURCE_ARTIFACT_PATH_INVALID")
    pure = PurePosixPath(value)
    if pure.is_absolute() or not pure.parts or any(part in {"", ".", ".."} for part in pure.parts):
        raise ValueError("SOURCE_ARTIFACT_PATH_UNSAFE")
    normalized = pure.as_posix()
    if not normalized.startswith("reports/external_acceptance/"):
        raise ValueError("SOURCE_ARTIFACT_OUTSIDE_ACCEPTANCE_ROOT")
    return normalized


def _has_reparse_component(root: Path, target: Path) -> bool:
    current = root.resolve()
    target = target.absolute()
    try:
        rel = target.relative_to(root.absolute())
    except ValueError:
        return True
    for part in rel.parts:
        current = current / part
        if not current.exists():
            continue
        try:
            mode = current.lstat().st_mode
        except OSError:
            return True
        if stat.S_ISLNK(mode):
            return True
        is_junction = getattr(current, "is_junction", None)
        if callable(is_junction) and is_junction():
            return True
    return False


def _strict_file(root: Path, rel: str) -> Path:
    normalized = _safe_rel(rel)
    target = (root / normalized).absolute()
    try:
        target.relative_to(root.absolute())
    except ValueError as exc:
        raise ValueError("SOURCE_ARTIFACT_OUTSIDE_ROOT") from exc
    if _has_reparse_component(root, target):
        raise ValueError("SOURCE_ARTIFACT_REPARSE_COMPONENT_FORBIDDEN")
    if not target.is_file():
        raise ValueError(f"SOURCE_ARTIFACT_MISSING:{normalized}")
    return target


def _load_json(path: Path, *, label: str) -> dict[str, Any]:
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise ValueError(f"{label}_INVALID_JSON:{type(exc).__name__}") from exc
    if not isinstance(loaded, dict):
        raise ValueError(f"{label}_INVALID_JSON_ROOT")
    return loaded


def _outside_root(path: Path, root: Path) -> bool:
    try:
        path.absolute().relative_to(root.absolute())
        return False
    except ValueError:
        return True


def _zip_info(name: str) -> zipfile.ZipInfo:
    info = zipfile.ZipInfo(filename=name, date_time=(1980, 1, 1, 0, 0, 0))
    info.compress_type = zipfile.ZIP_STORED
    info.create_system = 3
    info.external_attr = (0o100644 & 0xFFFF) << 16
    return info


def _publish_no_replace(temp_path: Path, output: Path) -> None:
    try:
        os.link(temp_path, output)
    except FileExistsError as exc:
        raise ValueError("OUTPUT_ALREADY_EXISTS") from exc
    except OSError as exc:
        raise ValueError(f"ATOMIC_PUBLISH_FAILED:{type(exc).__name__}") from exc
    finally:
        try:
            temp_path.unlink(missing_ok=True)
        except OSError:
            pass


def _write_json_exclusive(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())


def build_bundle(
    *,
    root: Path,
    candidate: str,
    acceptance_environment_id: str,
    topology_hash: str,
    output: Path,
) -> dict[str, Any]:
    root = root.resolve()
    output = output.absolute()
    candidate = candidate.strip().lower()
    topology = topology_hash.strip().lower()
    environment_id = acceptance_environment_id.strip()
    temp_path: Path | None = None

    try:
        if not GIT_SHA_RE.fullmatch(candidate):
            raise ValueError("CANDIDATE_SHA_INVALID")
        current = _git_sha(root)
        if current != candidate:
            raise ValueError(f"LOCAL_HEAD_SHA_MISMATCH:{current}")
        if not environment_id:
            raise ValueError("ACCEPTANCE_ENVIRONMENT_ID_MISSING")
        if not SHA256_RE.fullmatch(topology):
            raise ValueError("ACCEPTANCE_TOPOLOGY_HASH_INVALID")
        if not output.is_absolute():
            raise ValueError("OUTPUT_PATH_MUST_BE_ABSOLUTE")
        output.parent.mkdir(parents=True, exist_ok=True)
        output = output.parent.resolve() / output.name
        if not _outside_root(output, root):
            raise ValueError("OUTPUT_MUST_BE_OUTSIDE_REPOSITORY")
        if output.exists():
            raise ValueError("OUTPUT_ALREADY_EXISTS")

        challenge_path = _strict_file(root, CHALLENGE_PATH)
        challenge = _load_json(challenge_path, label="RELEASE_CHALLENGE")
        challenge_sha = _sha_file(challenge_path)
        challenge_id = challenge.get("challenge_id")
        if challenge.get("classification") != "EXTERNAL_ACCEPTANCE_RELEASE_CHALLENGE":
            raise ValueError("RELEASE_CHALLENGE_CLASSIFICATION_INVALID")
        if str(challenge.get("git_commit_sha", "")).lower() != candidate:
            raise ValueError("RELEASE_CHALLENGE_CANDIDATE_MISMATCH")
        if not isinstance(challenge_id, str) or len(challenge_id) < 16:
            raise ValueError("RELEASE_CHALLENGE_ID_INVALID")

        environment_hash = hashlib.sha256(environment_id.encode()).hexdigest()
        source_paths: dict[str, Path] = {CHALLENGE_PATH: challenge_path}
        source_artifact_paths: set[str] = set()

        for receipt_rel, classification in REQUIRED_RECEIPTS.items():
            receipt_path = _strict_file(root, receipt_rel)
            receipt = _load_json(receipt_path, label="CAMPAIGN_RECEIPT")
            if receipt.get("schema_version") != "1.0":
                raise ValueError(f"CAMPAIGN_RECEIPT_SCHEMA_INVALID:{receipt_rel}")
            if receipt.get("classification") != classification:
                raise ValueError(f"CAMPAIGN_RECEIPT_CLASSIFICATION_INVALID:{receipt_rel}")
            if receipt.get("real_system") is not True or receipt.get("executed") is not True:
                raise ValueError(f"CAMPAIGN_RECEIPT_NOT_REAL_EXECUTED:{receipt_rel}")
            if str(receipt.get("git_commit_sha", "")).lower() != candidate:
                raise ValueError(f"CAMPAIGN_RECEIPT_CANDIDATE_MISMATCH:{receipt_rel}")
            bound = receipt.get("release_challenge") if isinstance(receipt.get("release_challenge"), dict) else {}
            if bound.get("challenge_id") != challenge_id or str(bound.get("sha256", "")).lower() != challenge_sha:
                raise ValueError(f"CAMPAIGN_RELEASE_CHALLENGE_BINDING_MISMATCH:{receipt_rel}")
            environment = receipt.get("environment") if isinstance(receipt.get("environment"), dict) else {}
            if environment.get("acceptance_environment_id_hash") != environment_hash:
                raise ValueError(f"CAMPAIGN_ENVIRONMENT_ID_MISMATCH:{receipt_rel}")
            if str(environment.get("topology_hash", "")).lower() != topology:
                raise ValueError(f"CAMPAIGN_TOPOLOGY_HASH_MISMATCH:{receipt_rel}")
            artifacts = receipt.get("source_artifacts")
            if not isinstance(artifacts, list) or not artifacts:
                raise ValueError(f"CAMPAIGN_SOURCE_ARTIFACTS_MISSING:{receipt_rel}")
            for row in artifacts:
                if not isinstance(row, dict):
                    raise ValueError(f"CAMPAIGN_SOURCE_ARTIFACT_INVALID:{receipt_rel}")
                source_rel = _safe_rel(str(row.get("path", "")))
                expected = str(row.get("sha256", "")).lower()
                if not SHA256_RE.fullmatch(expected):
                    raise ValueError(f"CAMPAIGN_SOURCE_ARTIFACT_SHA_INVALID:{source_rel}")
                source_path = _strict_file(root, source_rel)
                if _sha_file(source_path) != expected:
                    raise ValueError(f"CAMPAIGN_SOURCE_ARTIFACT_HASH_MISMATCH:{source_rel}")
                source_paths[source_rel] = source_path
                source_artifact_paths.add(source_rel)
            source_paths[receipt_rel] = receipt_path

        file_hashes = {rel: _sha_file(path) for rel, path in sorted(source_paths.items())}
        manifest = {
            "schema_version": "1.0",
            "classification": BUNDLE_CLASSIFICATION,
            "candidate_sha": candidate,
            "acceptance_environment_id": environment_id,
            "topology_hash": topology,
            "files": file_hashes,
            "builder": {
                "classification": RECEIPT_CLASSIFICATION,
                "source_file_count": len(source_paths),
                "referenced_source_artifact_count": len(source_artifact_paths),
            },
        }
        manifest_bytes = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8")

        temp_path = output.parent / f".{output.name}.phase252-{uuid.uuid4().hex}.tmp"
        with zipfile.ZipFile(temp_path, mode="x", compression=zipfile.ZIP_STORED, allowZip64=True) as archive:
            archive.writestr(_zip_info(MANIFEST_NAME), manifest_bytes)
            for rel, path in sorted(source_paths.items()):
                data = path.read_bytes()
                if _sha_bytes(data) != file_hashes[rel]:
                    raise ValueError(f"SOURCE_CHANGED_DURING_BUILD:{rel}")
                archive.writestr(_zip_info(rel), data)

        with temp_path.open("rb+") as handle:
            os.fsync(handle.fileno())

        with zipfile.ZipFile(temp_path, "r") as archive:
            names = [info.filename for info in archive.infolist() if not info.is_dir()]
            expected_names = [MANIFEST_NAME, *sorted(source_paths)]
            if names != expected_names:
                raise ValueError("BUILT_ARCHIVE_MEMBER_SET_MISMATCH")
            loaded_manifest = json.loads(archive.read(MANIFEST_NAME).decode("utf-8"))
            if loaded_manifest != manifest:
                raise ValueError("BUILT_ARCHIVE_MANIFEST_MISMATCH")
            for rel, expected in file_hashes.items():
                if _sha_bytes(archive.read(rel)) != expected:
                    raise ValueError(f"BUILT_ARCHIVE_MEMBER_HASH_MISMATCH:{rel}")

        _publish_no_replace(temp_path, output)
        temp_path = None
        digest = _sha_file(output)
        return {
            "schema_version": "1.0",
            "classification": RECEIPT_CLASSIFICATION,
            "verified": True,
            "candidate_sha": candidate,
            "bundle_path": str(output),
            "bundle_sha256": digest,
            "acceptance_environment_id_sha256": environment_hash,
            "topology_hash": topology,
            "file_count": len(source_paths),
            "referenced_source_artifact_count": len(source_artifact_paths),
            "atomic_publish": True,
            "live_enabled": False,
            "production_ready": False,
            "problems": [],
            "truth_policy": "This receipt proves only an atomically published exact-SHA campaign evidence transport bundle. It never enables LIVE trading.",
        }
    except (OSError, ValueError, json.JSONDecodeError, zipfile.BadZipFile, zipfile.LargeZipFile) as exc:
        if temp_path is not None:
            try:
                temp_path.unlink(missing_ok=True)
            except OSError:
                pass
        return {
            "schema_version": "1.0",
            "classification": RECEIPT_CLASSIFICATION,
            "verified": False,
            "candidate_sha": candidate,
            "bundle_path": str(output),
            "live_enabled": False,
            "production_ready": False,
            "problems": [str(exc) or type(exc).__name__],
        }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build and atomically publish an exact-SHA campaign evidence transfer bundle")
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--acceptance-environment-id", required=True)
    parser.add_argument("--topology-hash", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--receipt", required=True)
    parser.add_argument("--root", default=str(ROOT))
    args = parser.parse_args()

    root = Path(args.root).expanduser().absolute()
    output = Path(args.output).expanduser().absolute()
    receipt_path = Path(args.receipt).expanduser().absolute()
    result = build_bundle(
        root=root,
        candidate=args.candidate,
        acceptance_environment_id=args.acceptance_environment_id,
        topology_hash=args.topology_hash,
        output=output,
    )
    try:
        _write_json_exclusive(receipt_path, result)
    except FileExistsError:
        print(json.dumps({**result, "verified": False, "problems": ["RECEIPT_ALREADY_EXISTS"]}, sort_keys=True))
        return 2
    except OSError as exc:
        print(json.dumps({**result, "verified": False, "problems": [f"RECEIPT_WRITE_FAILED:{type(exc).__name__}"]}, sort_keys=True))
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0 if result.get("verified") is True else 2


if __name__ == "__main__":
    raise SystemExit(main())
