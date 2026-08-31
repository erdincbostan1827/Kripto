from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _content_set(entries: list[dict]) -> str:
    normalized = [
        {"path": row["path"], "sha256": row["sha256"], "size": row["size"], "executable": row["executable"]}
        for row in sorted(entries, key=lambda item: item["path"])
    ]
    raw = json.dumps(normalized, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def _package_root(root: Path) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    payload = root / "README.md"
    payload.write_text("phase168\n", encoding="utf-8")
    row = {"path": "README.md", "sha256": _sha(payload), "size": payload.stat().st_size, "executable": False}
    manifest = {
        "schema_version": "2.0",
        "package_role": "SOURCE_RELEASE_ARCHIVE",
        "file_count": 1,
        "content_set_sha256": _content_set([row]),
        "source_identity": {"git_commit_sha": "a" * 40},
        "files": [row],
    }
    (root / "PACKAGE_MANIFEST.json").write_text(json.dumps(manifest), encoding="utf-8")
    return root


def test_source_identity_cli_honors_explicit_root(tmp_path: Path) -> None:
    package_root = _package_root(tmp_path / "package")
    wrong_cwd = tmp_path / "wrong"
    wrong_cwd.mkdir()
    script = Path(__file__).resolve().parents[2] / "scripts" / "verify_source_package_identity.py"
    proc = subprocess.run(
        [sys.executable, str(script), "--root", str(package_root)],
        cwd=wrong_cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    result = json.loads(proc.stdout)
    assert result["verified"] is True
    assert result["git_commit_sha"] == "a" * 40


def test_source_identity_cli_rejects_unknown_arguments(tmp_path: Path) -> None:
    package_root = _package_root(tmp_path / "package")
    script = Path(__file__).resolve().parents[2] / "scripts" / "verify_source_package_identity.py"
    proc = subprocess.run(
        [sys.executable, str(script), "--root", str(package_root), "--definitely-not-a-real-option"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert proc.returncode == 2
    assert "unrecognized arguments" in proc.stderr
