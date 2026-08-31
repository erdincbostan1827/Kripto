from __future__ import annotations

import hashlib
import json
import re
import tomllib
import uuid
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
_EXACT_PY = re.compile(r"^(?P<name>[A-Za-z0-9_.-]+)(?:\[[^\]]+\])?==(?P<version>.+)$")


def _sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _component_ref(ecosystem: str, name: str, version: str, scope: str) -> str:
    return f"urn:ctp:dependency:{ecosystem}:{scope}:{name}@{version}"


def _pypi_component(spec: str, scope: str) -> dict:
    match = _EXACT_PY.fullmatch(spec)
    if match:
        name = match.group("name")
        version = match.group("version")
    else:
        name = re.split(r"[<>=!~\[]", spec, maxsplit=1)[0]
        version = spec
    normalized = name.replace("_", "-").lower()
    return {
        "type": "library",
        "bom-ref": _component_ref("pypi", normalized, version, scope),
        "name": normalized,
        "version": version,
        "purl": f"pkg:pypi/{quote(normalized, safe='.-_')}@{quote(version, safe='.-_+')}",
        "resolved": False,
        "properties": [
            {"name": "ctp:dependency:ecosystem", "value": "pypi"},
            {"name": "ctp:dependency:scope", "value": scope},
            {"name": "ctp:dependency:direct", "value": "true"},
            {"name": "ctp:dependency:resolved_transitively", "value": "false"},
            {"name": "ctp:dependency:source_spec", "value": spec},
        ],
    }


def _npm_component(name: str, version: str, scope: str) -> dict:
    encoded_name = quote(name, safe="/")
    return {
        "type": "library",
        "bom-ref": _component_ref("npm", name, version, scope),
        "name": name,
        "version": version,
        "purl": f"pkg:npm/{encoded_name}@{quote(version, safe='.-_+')}",
        "resolved": False,
        "properties": [
            {"name": "ctp:dependency:ecosystem", "value": "npm"},
            {"name": "ctp:dependency:scope", "value": scope},
            {"name": "ctp:dependency:direct", "value": "true"},
            {"name": "ctp:dependency:resolved_transitively", "value": "false"},
        ],
    }


def _python_components(pyproject: Path) -> list[dict]:
    doc = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    project = doc.get("project", {})
    rows: list[dict] = []
    for spec in project.get("dependencies", []):
        rows.append(_pypi_component(spec, "runtime"))
    optional = project.get("optional-dependencies", {})
    for group, specs in sorted(optional.items()):
        for spec in specs:
            rows.append(_pypi_component(spec, f"optional:{group}"))
    build = doc.get("build-system", {})
    for spec in build.get("requires", []):
        rows.append(_pypi_component(spec, "build"))
    return rows


def _npm_components(package_json: Path) -> list[dict]:
    doc = json.loads(package_json.read_text(encoding="utf-8"))
    rows: list[dict] = []
    for section in ("dependencies", "devDependencies", "optionalDependencies", "peerDependencies"):
        for name, version in sorted((doc.get(section) or {}).items()):
            rows.append(_npm_component(name, version, section))
    return rows


def generate(root: Path = ROOT) -> dict:
    pyproject = root / "pyproject.toml"
    package = root / "frontend/package.json"
    components = [*_python_components(pyproject), *_npm_components(package)]
    components = sorted(components, key=lambda row: row["bom-ref"])
    source_fingerprint = {
        "pyproject_sha256": _sha(pyproject),
        "frontend_package_sha256": _sha(package),
    }
    serial_payload = json.dumps(
        {"components": components, "source_fingerprint": source_fingerprint},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    serial = uuid.uuid5(uuid.NAMESPACE_URL, "urn:ctp:sbom:" + hashlib.sha256(serial_payload).hexdigest())
    return {
        "bomFormat": "CycloneDX",
        "specVersion": "1.6",
        "serialNumber": f"urn:uuid:{serial}",
        "version": 1,
        "metadata": {
            "classification": "DIRECT_DEPENDENCY_INVENTORY_NOT_SUPPLY_CHAIN_ACCEPTANCE",
            "resolved_dependency_lock": False,
            "transitive_dependencies_resolved": False,
            "vulnerability_scan_performed": False,
            "pyproject_sha256": source_fingerprint["pyproject_sha256"],
            "frontend_package_sha256": source_fingerprint["frontend_package_sha256"],
            "component": {
                "type": "application",
                "name": "crypto-trading-platform-v51",
                "version": "0.3.0",
            },
            "properties": [
                {
                    "name": "ctp:sbom:classification",
                    "value": "DIRECT_DEPENDENCY_INVENTORY_NOT_FULL_SUPPLY_CHAIN_ACCEPTANCE",
                },
                {"name": "ctp:sbom:resolved_dependency_lock", "value": "false"},
                {"name": "ctp:sbom:transitive_dependencies_resolved", "value": "false"},
                {"name": "ctp:sbom:vulnerability_scan_performed", "value": "false"},
                {"name": "ctp:sbom:pyproject_sha256", "value": source_fingerprint["pyproject_sha256"]},
                {"name": "ctp:sbom:frontend_package_sha256", "value": source_fingerprint["frontend_package_sha256"]},
            ],
        },
        "components": components,
    }


def main() -> int:
    out = ROOT / "reports/SBOM.local.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    doc = generate(ROOT)
    out.write_text(json.dumps(doc, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    print(
        f"LOCAL_SBOM_WRITTEN={out.relative_to(ROOT)} components={len(doc['components'])} "
        "classification=DIRECT_ONLY unresolved_transitive=true vulnerability_scan=false"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
