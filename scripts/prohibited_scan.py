from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

PROHIBITED_PATTERN = re.compile(r"\b(TODO|FIXME|NotImplementedError)\b")
EXCLUDED_DIRS = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "build",
    "coverage",
    "dist",
    "node_modules",
}
SOURCE_ROOTS: tuple[tuple[str, frozenset[str]], ...] = (
    ("backend", frozenset({".py"})),
    ("frontend", frozenset({".ts", ".tsx"})),
)


def _is_excluded(path: Path, repository_root: Path) -> bool:
    try:
        relative = path.relative_to(repository_root)
    except ValueError:
        relative = path
    return any(part in EXCLUDED_DIRS for part in relative.parts)


def iter_source_files(repository_root: Path = Path(".")):
    root = repository_root.resolve()
    for source_root, suffixes in SOURCE_ROOTS:
        base = root / source_root
        if not base.is_dir():
            continue
        for path in base.rglob("*"):
            if not path.is_file() or path.suffix not in suffixes:
                continue
            if _is_excluded(path, root):
                continue
            yield path


def scan_repository(repository_root: Path = Path(".")) -> list[str]:
    root = repository_root.resolve()
    bad: list[str] = []
    for path in iter_source_files(root):
        text = path.read_text(encoding="utf-8")
        display = path.relative_to(root).as_posix()
        if PROHIBITED_PATTERN.search(text):
            bad.append(display)
        if path.suffix == ".py":
            tree = ast.parse(text, filename=display)
            for node in ast.walk(tree):
                if isinstance(node, ast.Pass):
                    bad.append(f"{display}:pass@{node.lineno}")
    return bad


def main() -> int:
    bad = scan_repository()
    print("PASS" if not bad else "\n".join(bad))
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
