from __future__ import annotations

import argparse
import importlib.metadata
import json
import os
import platform
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports" / "CI_TOOLCHAIN_RECEIPT.json"
PYTHON_PACKAGES = (
    "uv",
    "pip-audit",
    "bandit",
    "semgrep",
    "cyclonedx-bom",
    "pip-licenses",
)


def _git_sha(root: Path) -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()


def _versions() -> dict[str, str]:
    versions: dict[str, str] = {}
    for name in PYTHON_PACKAGES:
        try:
            versions[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError as exc:
            raise RuntimeError(f"REQUIRED_TOOL_PACKAGE_MISSING:{name}") from exc
    return versions


def _ci_context() -> dict[str, str | None]:
    return {
        "repository": os.getenv("GITHUB_REPOSITORY") or None,
        "run_id": os.getenv("GITHUB_RUN_ID") or None,
        "run_attempt": os.getenv("GITHUB_RUN_ATTEMPT") or None,
        "workflow_ref": os.getenv("GITHUB_WORKFLOW_REF") or None,
    }


def create(root: Path = ROOT, output: Path | None = None) -> dict:
    out = output or (root / "reports" / "CI_TOOLCHAIN_RECEIPT.json")
    payload = {
        "schema_version": "1.0",
        "classification": "CI_TOOLCHAIN_VERSION_RECEIPT",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "git_commit_sha": _git_sha(root),
        "python_version": platform.python_version(),
        "python_packages": _versions(),
        "ci_context": _ci_context(),
        "truth_policy": "The real-target acceptance runner must install and verify these exact Python tool versions before consuming CI scanner/build evidence.",
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def load(path: Path = OUT) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != "1.0" or payload.get("classification") != "CI_TOOLCHAIN_VERSION_RECEIPT":
        raise ValueError("CI_TOOLCHAIN_RECEIPT_INVALID")
    packages = payload.get("python_packages")
    if not isinstance(packages, dict) or set(packages) != set(PYTHON_PACKAGES):
        raise ValueError("CI_TOOLCHAIN_PACKAGE_SET_INVALID")
    for name, version in packages.items():
        if not isinstance(version, str) or not version.strip() or any(ch.isspace() for ch in version):
            raise ValueError(f"CI_TOOLCHAIN_VERSION_INVALID:{name}")
    return payload


def pip_specs(path: Path = OUT) -> list[str]:
    payload = load(path)
    packages = payload["python_packages"]
    return [f"{name}=={packages[name]}" for name in PYTHON_PACKAGES]


def verify(
    path: Path = OUT,
    *,
    root: Path = ROOT,
    expected_git_sha: str | None = None,
    verify_installed: bool = False,
) -> dict:
    problems: list[str] = []
    try:
        payload = load(path)
    except Exception as exc:
        return {"verified": False, "problems": [f"CI_TOOLCHAIN_RECEIPT_INVALID:{type(exc).__name__}"]}
    declared_git = payload.get("git_commit_sha")
    try:
        actual_git = _git_sha(root)
    except Exception:
        actual_git = None
        problems.append("CI_TOOLCHAIN_GIT_UNAVAILABLE")
    if declared_git != actual_git:
        problems.append("CI_TOOLCHAIN_GIT_MISMATCH")
    if expected_git_sha and declared_git != expected_git_sha:
        problems.append("CI_TOOLCHAIN_EXPECTED_GIT_MISMATCH")
    if verify_installed:
        try:
            installed = _versions()
        except Exception as exc:
            problems.append(str(exc))
            installed = {}
        for name, expected in payload.get("python_packages", {}).items():
            if installed.get(name) != expected:
                problems.append(f"CI_TOOLCHAIN_INSTALLED_VERSION_MISMATCH:{name}")
    return {
        "verified": not problems,
        "problems": problems,
        "git_commit_sha": declared_git,
        "python_packages": payload.get("python_packages", {}),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("create", "verify", "pip-specs"))
    parser.add_argument("--expected-git-sha")
    parser.add_argument("--verify-installed", action="store_true")
    args = parser.parse_args()
    try:
        if args.mode == "create":
            result = create()
            print(json.dumps({"created": True, "git_commit_sha": result["git_commit_sha"], "packages": result["python_packages"]}, sort_keys=True))
            return 0
        if args.mode == "pip-specs":
            print("\n".join(pip_specs()))
            return 0
        result = verify(expected_git_sha=args.expected_git_sha, verify_installed=args.verify_installed)
        print(json.dumps(result, sort_keys=True))
        return 0 if result["verified"] else 2
    except Exception as exc:
        print(json.dumps({"verified": False, "problems": [f"{type(exc).__name__}:{exc}"]}, sort_keys=True))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
