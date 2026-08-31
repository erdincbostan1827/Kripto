from __future__ import annotations

import json
import stat
import zipfile
from pathlib import Path

import pytest

from scripts.extract_source_package import extract
from scripts.generate_local_sbom import generate as generate_local_sbom
from scripts.package_release import build_release, make_manifest, verify_archive
from scripts.verify_dependency_policy import verify as verify_dependency_policy
from scripts.verify_source_package_identity import verify_source_package_identity


def test_release_excludes_coverage_variants_and_tsbuildinfo(tmp_path: Path):
    root = tmp_path / "project"
    root.mkdir()
    (root / "app.py").write_text("x=1\n", encoding="utf-8")
    (root / ".coverage.phase100").write_bytes(b"ephemeral")
    (root / "frontend").mkdir()
    (root / "frontend/tsconfig.app.tsbuildinfo").write_text("cache", encoding="utf-8")
    manifest = make_manifest(root)
    paths = {row["path"] for row in manifest["files"]}
    assert "app.py" in paths
    assert ".coverage.phase100" not in paths
    assert "frontend/tsconfig.app.tsbuildinfo" not in paths


def test_archive_rejects_casefold_collision_before_extract(tmp_path: Path):
    package = tmp_path / "bad.zip"
    with zipfile.ZipFile(package, "w") as zf:
        zf.writestr("project/Foo.py", b"a")
        zf.writestr("project/foo.py", b"b")
    with pytest.raises(ValueError, match="PORTABILITY_COLLISION"):
        extract(package, tmp_path / "out")
    assert not (tmp_path / "out/project/Foo.py").exists()


def test_archive_rejects_backslash_member_before_extract(tmp_path: Path):
    package = tmp_path / "bad.zip"
    with zipfile.ZipFile(package, "w") as zf:
        zf.writestr(r"project\..\escape.txt", b"x")
    with pytest.raises(ValueError, match="PORTABILITY_INVALID_SEPARATOR_OR_NUL"):
        extract(package, tmp_path / "out")


def test_archive_rejects_symlink_member_before_extract(tmp_path: Path):
    package = tmp_path / "bad.zip"
    info = zipfile.ZipInfo("project/link")
    info.create_system = 3
    info.external_attr = (stat.S_IFLNK | 0o777) << 16
    with zipfile.ZipFile(package, "w") as zf:
        zf.writestr(info, b"../../escape")
    with pytest.raises(ValueError, match="SPECIAL_FILE_TYPE"):
        extract(package, tmp_path / "out")


def test_archive_rejects_extreme_compression_ratio(tmp_path: Path):
    package = tmp_path / "bad.zip"
    with zipfile.ZipFile(package, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        zf.writestr("project/bomb.txt", b"0" * (2 * 1024 * 1024))
    with pytest.raises(ValueError, match="COMPRESSION_RATIO_LIMIT"):
        extract(package, tmp_path / "out")


def test_package_identity_rejects_unexpected_post_extract_file(tmp_path: Path):
    root = tmp_path / "project"
    root.mkdir()
    (root / "a.txt").write_text("safe\n", encoding="utf-8")
    archive = tmp_path / "source.zip"
    build_release(root, archive)
    out = tmp_path / "out"
    extract(archive, out)
    extracted = out / root.name
    (extracted / "injected.py").write_text("print('unexpected')\n", encoding="utf-8")
    result = verify_source_package_identity(extracted)
    assert result["verified"] is False
    assert "PACKAGE_UNEXPECTED_FILE:injected.py" in result["problems"]


def test_package_identity_rejects_expected_file_replaced_by_symlink(tmp_path: Path):
    root = tmp_path / "project"
    root.mkdir()
    (root / "a.txt").write_text("safe\n", encoding="utf-8")
    archive = tmp_path / "source.zip"
    build_release(root, archive)
    out = tmp_path / "out"
    extract(archive, out)
    extracted = out / root.name
    target = tmp_path / "external.txt"
    target.write_text("safe\n", encoding="utf-8")
    (extracted / "a.txt").unlink()
    try:
        (extracted / "a.txt").symlink_to(target)
    except OSError:
        pytest.skip("symlink creation unavailable")
    result = verify_source_package_identity(extracted)
    assert result["verified"] is False
    assert "PACKAGE_FILE_SYMLINK:a.txt" in result["problems"]


def test_archive_rejects_manifest_file_count_tamper(tmp_path: Path):
    root = tmp_path / "project"
    root.mkdir()
    (root / "a.txt").write_text("safe\n", encoding="utf-8")
    archive = tmp_path / "source.zip"
    build_release(root, archive)
    modified = tmp_path / "modified.zip"
    with zipfile.ZipFile(archive) as src, zipfile.ZipFile(modified, "w") as dst:
        for info in src.infolist():
            data = src.read(info)
            if info.filename.endswith("/PACKAGE_MANIFEST.json"):
                doc = json.loads(data)
                doc["file_count"] += 1
                data = (json.dumps(doc, sort_keys=True) + "\n").encode()
            dst.writestr(info, data)
    result = verify_archive(modified)
    assert "MANIFEST_FILE_COUNT_MISMATCH" in result["mismatches"]


def test_dependency_policy_passes_current_exact_manifests(tmp_path: Path):
    (tmp_path / "frontend").mkdir()
    (tmp_path / "pyproject.toml").write_text(
        '[project]\ndependencies=["fastapi==1.2.3"]\n[project.optional-dependencies]\ntest=["pytest==9.0.2"]\n'
        '[build-system]\nrequires=["setuptools==82.0.1"]\nbuild-backend="setuptools.build_meta"\n',
        encoding="utf-8",
    )
    (tmp_path / "frontend/package.json").write_text(
        '{"dependencies":{"react":"19.2.8"},"devDependencies":{"vite":"8.2.2"},"scripts":{"build":"vite build"}}',
        encoding="utf-8",
    )
    result = verify_dependency_policy(tmp_path)
    assert result["verified"] is True
    assert result["python_specs_checked"] == 3
    assert result["npm_specs_checked"] == 2


def test_dependency_policy_rejects_ranges_and_lifecycle_scripts(tmp_path: Path):
    (tmp_path / "frontend").mkdir()
    (tmp_path / "pyproject.toml").write_text(
        '[project]\ndependencies=["fastapi>=1.0"]\n[build-system]\nrequires=["setuptools==82.0.1"]\nbuild-backend="setuptools.build_meta"\n',
        encoding="utf-8",
    )
    (tmp_path / "frontend/package.json").write_text(
        '{"dependencies":{"react":"^19.0.0"},"scripts":{"postinstall":"node x.js"}}',
        encoding="utf-8",
    )
    result = verify_dependency_policy(tmp_path)
    assert result["verified"] is False
    assert any(p.startswith("PYTHON_NOT_EXACT_PIN") for p in result["problems"])
    assert any(p.startswith("NPM_NOT_EXACT_PIN") for p in result["problems"])
    assert "NPM_LIFECYCLE_SCRIPT_REQUIRES_REVIEW:postinstall" in result["problems"]


def test_local_sbom_is_deterministic_and_direct_only(tmp_path: Path):
    (tmp_path / "frontend").mkdir()
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname="demo"\nversion="1.0.0"\ndependencies=["fastapi==1.2.3"]\n'
        '[project.optional-dependencies]\ntest=["pytest==9.0.2"]\n'
        '[build-system]\nrequires=["setuptools==82.0.1"]\nbuild-backend="setuptools.build_meta"\n',
        encoding="utf-8",
    )
    (tmp_path / "frontend/package.json").write_text(
        '{"dependencies":{"react":"19.2.8"},"devDependencies":{"vite":"8.2.2"}}',
        encoding="utf-8",
    )
    first = generate_local_sbom(tmp_path)
    second = generate_local_sbom(tmp_path)
    assert first == second
    assert first["bomFormat"] == "CycloneDX"
    assert first["specVersion"] == "1.6"
    assert len(first["components"]) == 5
    properties = {p["name"]: p["value"] for p in first["metadata"]["properties"]}
    assert properties["ctp:sbom:transitive_dependencies_resolved"] == "false"
    assert properties["ctp:sbom:vulnerability_scan_performed"] == "false"
