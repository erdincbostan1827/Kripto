from __future__ import annotations

import json
import zipfile
from pathlib import Path

from scripts.package_release import build_release, verify_archive


def test_release_archive_excludes_secrets_and_caches_and_verifies_hashes(tmp_path: Path):
    root = tmp_path / "project"
    root.mkdir()
    root.joinpath("backend").mkdir()
    root.joinpath("backend/app.py").write_text("print('safe')\n", encoding="utf-8")
    root.joinpath("secrets").mkdir()
    root.joinpath("secrets/live_key").write_text("must-not-ship", encoding="utf-8")
    root.joinpath("__pycache__").mkdir()
    root.joinpath("__pycache__/x.pyc").write_bytes(b"cache")
    archive = tmp_path / "release.zip"

    built, manifest = build_release(root=root, archive=archive)
    assert manifest["secrets_included"] is False
    assert verify_archive(built) == {"forbidden": [], "mismatches": []}
    with zipfile.ZipFile(built) as zf:
        names = zf.namelist()
        assert any(name.endswith("backend/app.py") for name in names)
        assert not any("secrets" in Path(name).parts for name in names)
        assert not any("__pycache__" in Path(name).parts for name in names)
        package_manifest = json.loads(zf.read(f"{root.name}/PACKAGE_MANIFEST.json"))
        assert package_manifest["file_count"] == 1
