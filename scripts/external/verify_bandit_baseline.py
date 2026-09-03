from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MANIFEST = ROOT / "config" / "bandit-baseline-manifest.json"


def _normalized_code(value: str) -> str:
    lines: list[str] = []
    for line in value.splitlines():
        lines.append(re.sub(r"^\s*\d+\s?", "", line).rstrip())
    return "\n".join(lines).strip()


def _canonical_finding(item: dict[str, Any]) -> dict[str, Any]:
    cwe = item.get("issue_cwe") or {}
    return {
        "filename": item.get("filename", ""),
        "test_id": item.get("test_id", ""),
        "test_name": item.get("test_name", ""),
        "issue_severity": item.get("issue_severity", ""),
        "issue_confidence": item.get("issue_confidence", ""),
        "issue_text": item.get("issue_text", ""),
        "issue_cwe_id": cwe.get("id", 0),
        "code": _normalized_code(str(item.get("code", ""))),
    }


def finding_set_sha256(results: list[dict[str, Any]]) -> str:
    canonical = [_canonical_finding(item) for item in results]
    canonical.sort(key=lambda item: json.dumps(item, sort_keys=True, separators=(",", ":")))
    payload = json.dumps(
        canonical,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def verify(report_path: Path, manifest_path: Path = DEFAULT_MANIFEST) -> list[str]:
    problems: list[str] = []
    report = json.loads(report_path.read_text(encoding="utf-8"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    if manifest.get("scanner") != "bandit" or manifest.get("scanner_version") != "1.9.4":
        problems.append("BANDIT_BASELINE_MANIFEST_SCANNER_MISMATCH")

    errors = report.get("errors") or []
    if errors:
        problems.append(f"BANDIT_SCANNER_ERRORS:{len(errors)}")

    results = report.get("results")
    if not isinstance(results, list):
        return problems + ["BANDIT_RESULTS_MISSING"]

    finding_count = len(results)
    if finding_count != int(manifest.get("finding_count", -1)):
        problems.append(
            f"BANDIT_FINDING_COUNT_CHANGED:expected={manifest.get('finding_count')}:actual={finding_count}"
        )

    medium_or_high = sum(
        1 for item in results if item.get("issue_severity") in {"MEDIUM", "HIGH"}
    )
    if medium_or_high != int(manifest.get("medium_or_high_count", -1)):
        problems.append(
            "BANDIT_MEDIUM_OR_HIGH_COUNT_CHANGED:"
            f"expected={manifest.get('medium_or_high_count')}:actual={medium_or_high}"
        )
    if medium_or_high:
        problems.append(f"BANDIT_MEDIUM_OR_HIGH_FINDINGS_PRESENT:{medium_or_high}")

    actual_digest = finding_set_sha256(results)
    expected_digest = str(manifest.get("finding_set_sha256", ""))
    if actual_digest != expected_digest:
        problems.append(
            f"BANDIT_FINDING_SET_CHANGED:expected={expected_digest}:actual={actual_digest}"
        )

    return problems


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("report", type=Path)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    args = parser.parse_args()

    problems = verify(args.report, args.manifest)
    if problems:
        print("\n".join(problems))
        print("PHASE225_BANDIT_BASELINE_GATE=FAIL")
        return 2

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    print("PHASE225_BANDIT_BASELINE_GATE=PASS")
    print(f"finding_count={manifest['finding_count']}")
    print(f"medium_or_high_count={manifest['medium_or_high_count']}")
    print(f"finding_set_sha256={manifest['finding_set_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
