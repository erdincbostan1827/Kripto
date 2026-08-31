from __future__ import annotations

import json
from hashlib import sha256
from pathlib import Path

from backend.app.release.evidence_ledger import append_entry, verify_ledger


def test_ledger_schema_version_is_verified(tmp_path: Path) -> None:
    path = tmp_path / "ledger.json"
    append_entry(path, manifest_sha256="a" * 64, challenge_id="challenge-12345678", git_commit_sha="b" * 40, profile="runtime")
    doc = json.loads(path.read_text())
    doc["schema_version"] = "999.0"
    path.write_text(json.dumps(doc))
    result = verify_ledger(path)
    assert not result["verified"]
    assert "LEDGER_SCHEMA_VERSION_INVALID" in result["problems"]


def test_external_verifier_source_requires_profile_binding() -> None:
    text = Path("scripts/verify_external_acceptance.py").read_text()
    assert 'expected_ledger_profile = "all-merged" if profile == "all" else profile' in text
    assert 'row.get("profile") == expected_ledger_profile' in text


def test_ledger_entry_hash_covers_profile() -> None:
    path = Path("backend/app/release/evidence_ledger.py")
    text = path.read_text()
    assert '"profile", "previous_hash"' in text
