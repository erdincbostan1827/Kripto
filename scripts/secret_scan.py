from __future__ import annotations

import re
from pathlib import Path

ROOTS = [Path("backend"), Path("frontend/src"), Path("scripts"), Path("docker"), Path(".github")]
TOP_LEVEL = [Path("docker-compose.yml"), Path("docker-compose.prod.yml"), Path("pyproject.toml"), Path(".env.example")]
TEXT_SUFFIXES = {".py", ".ts", ".tsx", ".js", ".mjs", ".json", ".yaml", ".yml", ".toml", ".conf", ".sh", ".ps1", ".example"}
ASSIGNMENT = re.compile(r"(?i)\b(api[_-]?key|api[_-]?secret|secret|token|password|authorization)\b\s*[:=]\s*[\"']([^\"']{8,})[\"']")
TOKEN_PATTERNS = [
    re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
]
ALLOW_MARKERS = ("EXAMPLE", "DUMMY", "TEST_", "CHANGEME", "PLACEHOLDER", "YOUR_", "<", "${", "os.getenv", "_FILE")


def files_to_scan():
    for root in ROOTS:
        if not root.exists():
            continue
        if root.is_file():
            yield root
        else:
            for path in root.rglob("*"):
                if path.is_file() and "node_modules" not in path.parts and "__pycache__" not in path.parts:
                    if path.suffix.lower() in TEXT_SUFFIXES or path.name in {"Dockerfile", "nginx.conf"}:
                        yield path
    yield from (p for p in TOP_LEVEL if p.exists())


def is_allowed(value: str, line: str, path: Path) -> bool:
    upper = f"{value} {line}".upper()
    if any(marker in upper for marker in ALLOW_MARKERS):
        return True
    if path.name == ".env.example" and not value.strip():
        return True
    return False


def main() -> int:
    findings: list[str] = []
    seen: set[Path] = set()
    for path in files_to_scan():
        if path in seen:
            continue
        seen.add(path)
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for lineno, line in enumerate(text.splitlines(), 1):
            for pattern in TOKEN_PATTERNS:
                if pattern.search(line):
                    findings.append(f"{path}:{lineno}: secret-like token pattern")
            match = ASSIGNMENT.search(line)
            if match and not is_allowed(match.group(2), line, path):
                findings.append(f"{path}:{lineno}: hard-coded {match.group(1)}-like literal")
    if findings:
        print("FAIL")
        print("\n".join(findings))
        return 1
    print(f"PASS files_scanned={len(seen)} findings=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
