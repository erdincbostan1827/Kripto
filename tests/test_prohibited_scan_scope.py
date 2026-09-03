from pathlib import Path

from scripts.prohibited_scan import scan_repository


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_generated_and_vendor_frontend_trees_are_excluded(tmp_path: Path) -> None:
    _write(tmp_path / "backend" / "app.py", "VALUE = 1\n")
    _write(tmp_path / "frontend" / "src" / "app.ts", "export const value = 1;\n")
    _write(
        tmp_path / "frontend" / "node_modules" / "vendor" / "index.d.ts",
        "// TODO: third-party declaration\n",
    )
    _write(
        tmp_path / "frontend" / "dist" / "bundle.ts",
        "// FIXME: generated bundle\n",
    )

    assert scan_repository(tmp_path) == []


def test_first_party_frontend_prohibited_marker_is_reported(tmp_path: Path) -> None:
    _write(tmp_path / "backend" / "app.py", "VALUE = 1\n")
    _write(tmp_path / "frontend" / "src" / "bad.ts", "// TODO: first-party debt\n")

    assert scan_repository(tmp_path) == ["frontend/src/bad.ts"]


def test_backend_pass_statement_is_reported(tmp_path: Path) -> None:
    _write(tmp_path / "backend" / "bad.py", "def unfinished():\n    pass\n")

    assert scan_repository(tmp_path) == ["backend/bad.py:pass@2"]
