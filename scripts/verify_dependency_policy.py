from __future__ import annotations

import json
import re
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYPROJECT = Path("pyproject.toml")
PACKAGE_JSON = Path("frontend/package.json")
REPORT = Path("reports/DEPENDENCY_POLICY.txt")

_PY_EXACT = re.compile(
    r"^[A-Za-z0-9_.-]+(?:\[[A-Za-z0-9_.-]+(?:,[A-Za-z0-9_.-]+)*\])?=="
    r"[A-Za-z0-9][A-Za-z0-9_.+!-]*$"
)
_NPM_EXACT = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$")
NPM_LIFECYCLE_SCRIPTS = {"preinstall", "install", "postinstall", "prepublish", "prepare"}


def _python_specs(doc: dict) -> list[tuple[str, str]]:
    specs: list[tuple[str, str]] = []
    project = doc.get("project") if isinstance(doc.get("project"), dict) else {}
    for value in project.get("dependencies", []):
        specs.append(("project.dependencies", value))
    optional = project.get("optional-dependencies") if isinstance(project.get("optional-dependencies"), dict) else {}
    for group, values in sorted(optional.items()):
        for value in values:
            specs.append((f"project.optional-dependencies.{group}", value))
    build = doc.get("build-system") if isinstance(doc.get("build-system"), dict) else {}
    for value in build.get("requires", []):
        specs.append(("build-system.requires", value))
    return specs


def verify(root: Path = ROOT) -> dict:
    problems: list[str] = []
    pyproject_path = root / PYPROJECT
    package_path = root / PACKAGE_JSON
    if not pyproject_path.is_file():
        problems.append(f"MISSING:{PYPROJECT}")
        py_doc = {}
    else:
        try:
            py_doc = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
        except Exception as exc:
            problems.append(f"INVALID_TOML:{type(exc).__name__}")
            py_doc = {}

    python_specs = _python_specs(py_doc)
    for section, spec in python_specs:
        if not isinstance(spec, str) or not _PY_EXACT.fullmatch(spec):
            problems.append(f"PYTHON_NOT_EXACT_PIN:{section}:{spec}")

    if not package_path.is_file():
        problems.append(f"MISSING:{PACKAGE_JSON}")
        npm_doc = {}
    else:
        try:
            npm_doc = json.loads(package_path.read_text(encoding="utf-8"))
        except Exception as exc:
            problems.append(f"INVALID_PACKAGE_JSON:{type(exc).__name__}")
            npm_doc = {}

    npm_specs: list[tuple[str, str, str]] = []
    for section in ("dependencies", "devDependencies", "optionalDependencies", "peerDependencies"):
        values = npm_doc.get(section, {})
        if values is None:
            continue
        if not isinstance(values, dict):
            problems.append(f"NPM_SECTION_INVALID:{section}")
            continue
        for name, version in sorted(values.items()):
            npm_specs.append((section, str(name), str(version)))
            if not isinstance(version, str) or not _NPM_EXACT.fullmatch(version):
                problems.append(f"NPM_NOT_EXACT_PIN:{section}:{name}:{version}")

    scripts = npm_doc.get("scripts", {})
    if isinstance(scripts, dict):
        for name in sorted(NPM_LIFECYCLE_SCRIPTS & set(scripts)):
            problems.append(f"NPM_LIFECYCLE_SCRIPT_REQUIRES_REVIEW:{name}")
    elif scripts is not None:
        problems.append("NPM_SCRIPTS_INVALID")

    return {
        "verified": not problems,
        "classification": "DIRECT_DEPENDENCY_MANIFEST_POLICY_ONLY_NOT_VULNERABILITY_SCAN",
        "python_specs_checked": len(python_specs),
        "npm_specs_checked": len(npm_specs),
        "lockfiles_present": {
            "uv.lock": (root / "uv.lock").is_file(),
            "frontend/package-lock.json": (root / "frontend/package-lock.json").is_file(),
        },
        "vulnerability_scan_performed": False,
        "transitive_dependencies_resolved": False,
        "problems": sorted(set(problems)),
    }


def render(result: dict) -> str:
    lines = [
        f"DEPENDENCY_MANIFEST_POLICY={'PASS' if result['verified'] else 'FAIL'}",
        f"classification={result['classification']}",
        f"python_specs_checked={result['python_specs_checked']}",
        f"npm_specs_checked={result['npm_specs_checked']}",
        f"uv_lock_present={str(result['lockfiles_present']['uv.lock']).lower()}",
        f"npm_lock_present={str(result['lockfiles_present']['frontend/package-lock.json']).lower()}",
        "vulnerability_scan_performed=false",
        "transitive_dependencies_resolved=false",
    ]
    for problem in result["problems"]:
        lines.append(f"- {problem}")
    return "\n".join(lines) + "\n"


def main() -> int:
    result = verify(ROOT)
    text = render(result)
    report = ROOT / REPORT
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0 if result["verified"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
