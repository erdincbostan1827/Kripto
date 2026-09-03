from __future__ import annotations

import json
import re
from hashlib import sha256
from pathlib import Path
from typing import Any

_SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}$")


def _sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _valid_sha256_hashes(component: dict[str, Any]) -> list[str]:
    hashes = component.get("hashes")
    if not isinstance(hashes, list):
        return []
    values: list[str] = []
    for item in hashes:
        if not isinstance(item, dict):
            continue
        algorithm = str(item.get("alg") or "").strip().upper().replace("_", "-")
        if algorithm not in {"SHA-256", "SHA256"}:
            continue
        content = str(item.get("content") or "").strip()
        if _SHA256_RE.fullmatch(content):
            values.append(content.lower())
    return values


def verify_cyclonedx_sbom(path: Path) -> dict[str, Any]:
    problems: list[str] = []
    if not path.is_file():
        return {"verified": False, "problems": ["SBOM_MISSING"], "components": 0}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"verified": False, "problems": [f"SBOM_INVALID_JSON:{type(exc).__name__}"], "components": 0}
    if payload.get("bomFormat") != "CycloneDX":
        problems.append("SBOM_NOT_CYCLONEDX")
    spec = payload.get("specVersion")
    if not isinstance(spec, str) or not spec.strip():
        problems.append("SBOM_SPEC_VERSION_MISSING")
    components = payload.get("components")
    if not isinstance(components, list) or not components:
        problems.append("SBOM_COMPONENTS_EMPTY")
        components = []
    for idx, item in enumerate(components, start=1):
        if not isinstance(item, dict):
            problems.append(f"SBOM_COMPONENT_INVALID:{idx}")
            continue
        if not str(item.get("name") or "").strip():
            problems.append(f"SBOM_COMPONENT_NAME_MISSING:{idx}")

        component_type = str(item.get("type") or "").strip().lower()
        if component_type == "file":
            bom_ref = str(item.get("bom-ref") or "").strip()
            if not bom_ref:
                problems.append(f"SBOM_FILE_BOM_REF_MISSING:{idx}")
            sha256_values = _valid_sha256_hashes(item)
            if not sha256_values:
                problems.append(f"SBOM_FILE_SHA256_MISSING:{idx}")
            elif bom_ref.lower().startswith("filesha256:"):
                referenced_digest = bom_ref.split(":", 1)[1].strip().lower()
                if referenced_digest not in sha256_values:
                    problems.append(f"SBOM_FILE_BOM_REF_HASH_MISMATCH:{idx}")
        elif not str(item.get("version") or "").strip():
            problems.append(f"SBOM_COMPONENT_VERSION_MISSING:{idx}")
    return {
        "verified": not problems,
        "problems": problems,
        "components": len(components),
        "spec_version": spec,
        "sha256": _sha(path),
    }


def verify_license_report(path: Path) -> dict[str, Any]:
    problems: list[str] = []
    if not path.is_file():
        return {"verified": False, "problems": ["LICENSE_REPORT_MISSING"], "packages": 0}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"verified": False, "problems": [f"LICENSE_REPORT_INVALID_JSON:{type(exc).__name__}"], "packages": 0}
    if not isinstance(payload, list) or not payload:
        return {"verified": False, "problems": ["LICENSE_REPORT_EMPTY"], "packages": 0}
    for idx, item in enumerate(payload, start=1):
        if not isinstance(item, dict):
            problems.append(f"LICENSE_ROW_INVALID:{idx}")
            continue
        name = item.get("Name") or item.get("name")
        version = item.get("Version") or item.get("version")
        license_name = item.get("License") or item.get("license") or item.get("LicenseExpression")
        if not str(name or "").strip():
            problems.append(f"LICENSE_NAME_MISSING:{idx}")
        if not str(version or "").strip():
            problems.append(f"LICENSE_VERSION_MISSING:{idx}")
        if not str(license_name or "").strip():
            problems.append(f"LICENSE_VALUE_MISSING:{idx}")
    return {
        "verified": not problems,
        "problems": problems,
        "packages": len(payload),
        "sha256": _sha(path),
    }


def verify_supply_chain_artifacts(sbom: Path, licenses: Path) -> dict[str, Any]:
    sbom_result = verify_cyclonedx_sbom(sbom)
    license_result = verify_license_report(licenses)
    problems = [*(f"SBOM:{p}" for p in sbom_result["problems"]), *(f"LICENSE:{p}" for p in license_result["problems"])]
    return {
        "classification": "SUPPLY_CHAIN_ARTIFACT_SEMANTIC_VERIFICATION",
        "verified": not problems,
        "problems": problems,
        "sbom": sbom_result,
        "license_report": license_result,
    }
