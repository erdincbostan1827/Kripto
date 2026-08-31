from __future__ import annotations

import json
import os
import zipfile
from pathlib import Path

from scripts.package_release import build_release, verify_archive


def test_release_archive_preserves_executable_mode(tmp_path: Path):
    root = tmp_path / "project"
    root.mkdir()
    script = root / "install.sh"
    script.write_text("#!/bin/sh\nexit 0\n")
    script.chmod(0o755)
    archive = tmp_path / "release.zip"
    built, manifest = build_release(root=root, archive=archive)
    row = next(x for x in manifest["files"] if x["path"] == "install.sh")
    assert row["executable"] is True
    assert verify_archive(built) == {"forbidden": [], "mismatches": []}
    with zipfile.ZipFile(built) as zf:
        member = zf.getinfo(f"{root.name}/install.sh")
        assert ((member.external_attr >> 16) & 0o111) != 0
