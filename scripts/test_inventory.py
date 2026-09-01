from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

_IMPORT_ROOT = Path(__file__).resolve().parents[1]
if str(_IMPORT_ROOT) not in sys.path:
    sys.path.insert(0, str(_IMPORT_ROOT))
from scripts.bounded_subprocess import run_captured, run_captured_bytes

ROOT = _IMPORT_ROOT
OUT_JSON = ROOT / "reports" / "TEST_INVENTORY.json"
OUT_TEXT = ROOT / "reports" / "TEST_COUNT.txt"
OUT_COLLECTION = ROOT / "reports" / "TEST_COLLECTION.txt"
REGRESSION = ROOT / "reports" / "local_acceptance" / "full_regression_manifest.json"


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git_sha(root: Path = ROOT) -> str | None:
    try:
        proc = run_captured_bytes(["git", "rev-parse", "HEAD"], cwd=root, timeout=10)
        if proc.returncode != 0:
            return None
        value = proc.stdout.decode("ascii", errors="ignore").strip().lower()
        return value if len(value) == 40 else None
    except Exception:
        return None


def parse_test_count_text(text: str) -> int | None:
    match = re.search(r"(\d+) tests collected", text)
    if match:
        return int(match.group(1))
    stripped = text.strip()
    if re.fullmatch(r"\d+", stripped):
        return int(stripped)
    grouped = re.findall(r"^tests/.+?:\s+(\d+)\s*$", text, re.M)
    return sum(map(int, grouped)) if grouped else None


def parse_collection(text: str) -> tuple[int, int]:
    rows = re.findall(r"^(tests/.+?):\s+(\d+)\s*$", text, re.M)
    if not rows:
        raise ValueError("COLLECTION_ROWS_NOT_FOUND")
    return sum(int(count) for _, count in rows), len(rows)


def read_verified(root: Path = ROOT) -> dict:
    path = root / "reports" / "TEST_INVENTORY.json"
    problems: list[str] = []
    if not path.is_file():
        return {"verified": False, "test_count": None, "test_file_count": None, "problems": ["TEST_INVENTORY_MISSING"]}
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {"verified": False, "test_count": None, "test_file_count": None, "problems": ["TEST_INVENTORY_INVALID_JSON"]}
    current = _git_sha(root)
    if doc.get("classification") != "FRESH_GIT_BOUND_TEST_INVENTORY":
        problems.append("CLASSIFICATION_INVALID")
    if current is None or doc.get("git_commit_sha") != current:
        problems.append("GIT_COMMIT_MISMATCH")
    test_count = doc.get("test_count")
    file_count = doc.get("test_file_count")
    if not isinstance(test_count, int) or test_count <= 0:
        problems.append("TEST_COUNT_INVALID")
    if not isinstance(file_count, int) or file_count <= 0:
        problems.append("TEST_FILE_COUNT_INVALID")
    collection_ref = doc.get("collection_reference")
    if not isinstance(collection_ref, str):
        problems.append("COLLECTION_REFERENCE_MISSING")
    else:
        cp = root / collection_ref
        if not cp.is_file() or _sha(cp) != doc.get("collection_sha256"):
            problems.append("COLLECTION_HASH_INVALID")
    regression_ref = doc.get("full_regression_reference")
    if not isinstance(regression_ref, str):
        problems.append("REGRESSION_REFERENCE_MISSING")
    else:
        rp = root / regression_ref
        if not rp.is_file() or _sha(rp) != doc.get("full_regression_sha256"):
            problems.append("REGRESSION_HASH_INVALID")
        else:
            try:
                regression = json.loads(rp.read_text(encoding="utf-8"))
                if regression.get("git_commit_sha") != current:
                    problems.append("REGRESSION_GIT_MISMATCH")
                if regression.get("status") != "PASS" or regression.get("problems") not in ([], None):
                    problems.append("REGRESSION_NOT_PASS")
                if regression.get("covered_test_file_count") != file_count:
                    problems.append("REGRESSION_FILE_COUNT_MISMATCH")
            except Exception:
                problems.append("REGRESSION_INVALID_JSON")
    return {
        "verified": not problems,
        "test_count": test_count,
        "test_file_count": file_count,
        "git_commit_sha": current,
        "problems": sorted(set(problems)),
        "inventory_sha256": _sha(path),
    }


def generate(*, timeout: int = 120) -> dict:
    current = _git_sha(ROOT)
    if current is None:
        raise RuntimeError("GIT_IDENTITY_UNAVAILABLE")
    proc = run_captured(["pytest", "--collect-only", "-q"], cwd=ROOT, timeout=timeout)
    if proc.returncode != 0:
        raise RuntimeError(f"PYTEST_COLLECTION_FAILED:{proc.returncode}")
    collection = proc.stdout or ""
    count, files = parse_collection(collection)
    if not REGRESSION.is_file():
        raise RuntimeError("FULL_REGRESSION_MANIFEST_MISSING")
    regression = json.loads(REGRESSION.read_text(encoding="utf-8"))
    if regression.get("git_commit_sha") != current or regression.get("status") != "PASS" or regression.get("problems") not in ([], None):
        raise RuntimeError("FULL_REGRESSION_NOT_CURRENT_PASS")
    if regression.get("covered_test_file_count") != files:
        raise RuntimeError(f"TEST_FILE_COUNT_MISMATCH:collection={files}:regression={regression.get('covered_test_file_count')}")
    OUT_COLLECTION.write_text(collection, encoding="utf-8")
    OUT_TEXT.write_text(f"{count} tests collected\n{files} test files collected\nclassification=FRESH_GIT_BOUND_TEST_INVENTORY\n", encoding="utf-8")
    payload = {
        "schema_version": "1.0",
        "classification": "FRESH_GIT_BOUND_TEST_INVENTORY",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "git_commit_sha": current,
        "test_count": count,
        "test_file_count": files,
        "collection_reference": str(OUT_COLLECTION.relative_to(ROOT)),
        "collection_sha256": _sha(OUT_COLLECTION),
        "full_regression_reference": str(REGRESSION.relative_to(ROOT)),
        "full_regression_sha256": _sha(REGRESSION),
    }
    OUT_JSON.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    verified = read_verified(ROOT)
    payload["verified"] = verified["verified"]
    payload["verification_problems"] = verified["problems"]
    return payload


def main() -> int:
    ap = argparse.ArgumentParser(description="Generate Git-bound test inventory from pytest collection and full regression evidence")
    ap.add_argument("--timeout", type=int, default=120)
    args = ap.parse_args()
    try:
        payload = generate(timeout=max(1, args.timeout))
    except Exception as exc:
        print(json.dumps({"verified": False, "error": str(exc)}, sort_keys=True))
        return 2
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload.get("verified") else 2


if __name__ == "__main__":
    raise SystemExit(main())
