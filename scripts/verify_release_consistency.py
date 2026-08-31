from __future__ import annotations

import json
import re
from pathlib import Path

try:
    from scripts.test_inventory import read_verified as read_test_inventory
except ModuleNotFoundError:
    from test_inventory import read_verified as read_test_inventory

ROOT = Path(__file__).resolve().parents[1]


def _json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _test_count(path: Path) -> int | None:
    machine = read_test_inventory(path.parents[1])
    if machine.get("verified"):
        return machine.get("test_count")
    if not path.is_file():
        return None
    text = path.read_text(encoding="utf-8", errors="ignore")
    match = re.search(r"(\d+) tests collected", text)
    if match:
        return int(match.group(1))
    stripped = text.strip()
    if re.fullmatch(r"\d+", stripped):
        return int(stripped)
    grouped = re.findall(r"^tests/.+?:\s+(\d+)\s*$", text, re.M)
    return sum(map(int, grouped)) if grouped else None


def verify(root: Path = ROOT) -> dict:
    release = _json(root / "RELEASE_MANIFEST.json")
    status = _json(root / "reports/PROJECT_STATUS.json")
    provenance = _json(root / "reports/LOCAL_SOURCE_PROVENANCE.json")
    tests = _test_count(root / "reports/TEST_COUNT.txt")
    problems: list[str] = []
    test_ev = release.get("test_evidence", {}) if isinstance(release.get("test_evidence"), dict) else {}

    release_count = test_ev.get("test_count")
    status_count = status.get("test_count")
    if tests is None:
        problems.append("TEST_COUNT_UNAVAILABLE")
    if release_count != tests:
        problems.append("RELEASE_TEST_COUNT_MISMATCH")
    if status_count != tests:
        problems.append("STATUS_TEST_COUNT_MISMATCH")

    coverage_fields = ("coverage_percent", "coverage_fresh", "coverage_classification")
    status_coverage = {
        "coverage_percent": status.get("backend_coverage_percent"),
        "coverage_fresh": status.get("coverage_fresh"),
        "coverage_classification": status.get("coverage_classification"),
    }
    for field in coverage_fields:
        if test_ev.get(field) != status_coverage.get(field):
            problems.append("STATUS_RELEASE_" + field.upper() + "_MISMATCH")

    release_sha = release.get("git_commit_sha")
    provenance_sha = provenance.get("git_commit_sha")
    if release_sha != provenance_sha:
        problems.append("RELEASE_PROVENANCE_GIT_MISMATCH")

    if release.get("default_mode") != "PAPER" or status.get("default_mode") != "PAPER":
        problems.append("DEFAULT_MODE_INCONSISTENT")
    if release.get("live_enabled") is not False or status.get("live_enabled") is not False:
        problems.append("LIVE_ENABLED_INCONSISTENT")
    if release.get("prod_live_status") != status.get("prod_live_status"):
        problems.append("PROD_LIVE_STATUS_MISMATCH")

    return {
        "schema_version": "1.0",
        "verified": not problems,
        "problems": sorted(problems),
        "test_count": tests,
        "git_commit_sha": release_sha,
        "coverage": {field: test_ev.get(field) for field in coverage_fields},
    }


def main() -> int:
    result = verify()
    out = ROOT / "reports" / "RELEASE_CONSISTENCY.json"
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0 if result["verified"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
