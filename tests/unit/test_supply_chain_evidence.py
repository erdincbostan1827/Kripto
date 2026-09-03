from __future__ import annotations

import json
from pathlib import Path

from backend.app.release.supply_chain_evidence import verify_cyclonedx_sbom


def _write_sbom(tmp_path: Path, component: dict[str, object]) -> Path:
    path = tmp_path / "sbom.cdx.json"
    path.write_text(
        json.dumps(
            {
                "bomFormat": "CycloneDX",
                "specVersion": "1.6",
                "components": [component],
            }
        ),
        encoding="utf-8",
    )
    return path


def test_package_component_requires_version(tmp_path: Path) -> None:
    result = verify_cyclonedx_sbom(
        _write_sbom(tmp_path, {"type": "library", "name": "example"})
    )
    assert result["verified"] is False
    assert "SBOM_COMPONENT_VERSION_MISSING:1" in result["problems"]


def test_package_component_with_version_passes(tmp_path: Path) -> None:
    result = verify_cyclonedx_sbom(
        _write_sbom(
            tmp_path,
            {"type": "library", "name": "example", "version": "1.2.3"},
        )
    )
    assert result["verified"] is True
    assert result["problems"] == []


def test_file_component_uses_sha256_identity_instead_of_version(tmp_path: Path) -> None:
    digest = "a" * 64
    result = verify_cyclonedx_sbom(
        _write_sbom(
            tmp_path,
            {
                "type": "file",
                "name": "uv.lock",
                "bom-ref": f"filesha256:{digest}",
                "hashes": [{"alg": "SHA-256", "content": digest}],
            },
        )
    )
    assert result["verified"] is True
    assert result["problems"] == []


def test_file_component_requires_bom_ref(tmp_path: Path) -> None:
    digest = "b" * 64
    result = verify_cyclonedx_sbom(
        _write_sbom(
            tmp_path,
            {
                "type": "file",
                "name": "uv.lock",
                "hashes": [{"alg": "SHA-256", "content": digest}],
            },
        )
    )
    assert result["verified"] is False
    assert "SBOM_FILE_BOM_REF_MISSING:1" in result["problems"]


def test_file_component_requires_valid_sha256(tmp_path: Path) -> None:
    result = verify_cyclonedx_sbom(
        _write_sbom(
            tmp_path,
            {
                "type": "file",
                "name": "uv.lock",
                "bom-ref": "filesha256:bad",
                "hashes": [{"alg": "SHA-256", "content": "bad"}],
            },
        )
    )
    assert result["verified"] is False
    assert "SBOM_FILE_SHA256_MISSING:1" in result["problems"]


def test_filesha256_bom_ref_must_match_declared_hash(tmp_path: Path) -> None:
    result = verify_cyclonedx_sbom(
        _write_sbom(
            tmp_path,
            {
                "type": "file",
                "name": "uv.lock",
                "bom-ref": f"filesha256:{'c' * 64}",
                "hashes": [{"alg": "SHA-256", "content": "d" * 64}],
            },
        )
    )
    assert result["verified"] is False
    assert "SBOM_FILE_BOM_REF_HASH_MISMATCH:1" in result["problems"]
