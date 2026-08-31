from __future__ import annotations

from pathlib import Path


class PathIntegrityError(ValueError):
    """Fail-closed path validation error for release/acceptance artifacts."""


def resolve_without_symlink_components(root: Path, value: str | Path) -> Path:
    """Resolve a path under root while rejecting lexical escape and any symlink component."""
    root_abs = root.absolute()
    if root_abs.is_symlink():
        raise PathIntegrityError("configured root must not be a symlink")
    candidate = Path(value)
    if not candidate.is_absolute():
        raw = str(value)
        if not candidate.parts or ".." in candidate.parts or "\\" in raw or "\x00" in raw:
            raise PathIntegrityError("unsafe relative path")
        candidate_abs = (root_abs / candidate).absolute()
    else:
        candidate_abs = candidate.absolute()
    try:
        rel = candidate_abs.relative_to(root_abs)
    except ValueError as exc:
        raise PathIntegrityError("path escapes configured root") from exc
    current = root_abs
    for part in rel.parts:
        current = current / part
        if current.is_symlink():
            raise PathIntegrityError("path contains symlink component")
    resolved = candidate_abs.resolve(strict=False)
    try:
        resolved.relative_to(root.resolve())
    except ValueError as exc:
        raise PathIntegrityError("resolved path escapes configured root") from exc
    return resolved


def strict_regular_file(root: Path, value: str | Path) -> Path:
    resolved = resolve_without_symlink_components(root, value)
    if not resolved.is_file():
        raise PathIntegrityError("path is not a regular file")
    return resolved
