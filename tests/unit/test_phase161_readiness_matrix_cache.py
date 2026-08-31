from __future__ import annotations

from pathlib import Path

import scripts.production_readiness_dossier as dossier


def test_matrix_cache_reuses_unchanged_document(monkeypatch) -> None:
    dossier._load_matrix_cached.cache_clear()
    calls = 0
    original = dossier.yaml.safe_load

    def counted(value):
        nonlocal calls
        calls += 1
        return original(value)

    monkeypatch.setattr(dossier.yaml, "safe_load", counted)
    first = dossier.build()
    second = dossier.build()
    assert first["p0_blocker_count"] == second["p0_blocker_count"]
    assert calls == 1


def test_matrix_cache_invalidates_on_file_signature_change(tmp_path: Path) -> None:
    dossier._load_matrix_cached.cache_clear()
    path = tmp_path / "matrix.yaml"
    path.write_text("requirements: []\n", encoding="utf-8")
    first = dossier._matrix_doc(path)
    path.write_text("requirements:\n  - requirement_id: X\n", encoding="utf-8")
    second = dossier._matrix_doc(path)
    assert first != second
