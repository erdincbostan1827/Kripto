from pathlib import Path

import yaml

from scripts.verify_source_locks import verify_source_locks

ROOT = Path(__file__).resolve().parents[2]


def test_phase220_section1_technology_profile_is_complete_with_committed_locks():
    profile = yaml.safe_load((ROOT / "architecture_profile.yaml").read_text(encoding="utf-8"))
    package = (ROOT / "frontend/package.json").read_text(encoding="utf-8")
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")

    assert profile
    assert '"react"' in package.lower()
    assert "fastapi" in pyproject.lower()

    locks = verify_source_locks(ROOT)
    assert locks["verified"] is True, locks["problems"]
    assert locks["repository_verified"] is True
    assert all(row["source_compliant"] for row in locks["locks"])
