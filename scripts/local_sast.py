from __future__ import annotations

import ast
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOTS = (ROOT / "backend", ROOT / "scripts", ROOT / "frontend" / "src")
EXCLUDED_NAMES = {"local_sast.py"}


@dataclass(frozen=True)
class Finding:
    rule_id: str
    severity: str
    path: str
    line: int
    message: str


class PythonVisitor(ast.NodeVisitor):
    def __init__(self, path: Path) -> None:
        self.path = path
        self.findings: list[Finding] = []

    def _add(self, node: ast.AST, rule_id: str, message: str, severity: str = "HIGH") -> None:
        self.findings.append(
            Finding(rule_id, severity, str(self.path.relative_to(ROOT)), getattr(node, "lineno", 1), message)
        )

    @staticmethod
    def _name(node: ast.AST) -> str:
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            base = PythonVisitor._name(node.value)
            return f"{base}.{node.attr}" if base else node.attr
        return ""

    def visit_Call(self, node: ast.Call) -> None:
        name = self._name(node.func)
        if name in {"eval", "exec"}:
            self._add(node, "PY-EVAL-EXEC", f"Dynamic code execution via {name}()")
        if name in {"os.system", "subprocess.getoutput", "subprocess.getstatusoutput"}:
            self._add(node, "PY-SHELL-EXEC", f"Shell execution via {name}")
        if name.startswith("subprocess."):
            for keyword in node.keywords:
                if keyword.arg == "shell" and isinstance(keyword.value, ast.Constant) and keyword.value.value is True:
                    self._add(node, "PY-SUBPROCESS-SHELL", "subprocess call uses shell=True")
        if name in {"pickle.loads", "pickle.load", "marshal.loads", "marshal.load"}:
            self._add(node, "PY-UNSAFE-DESERIALIZE", f"Unsafe deserialization via {name}")
        if name in {"yaml.load", "yaml.unsafe_load"}:
            self._add(node, "PY-UNSAFE-YAML", f"Potentially unsafe YAML deserialization via {name}")
        self.generic_visit(node)


_TS_RULES: tuple[tuple[str, re.Pattern[str], str], ...] = (
    ("TS-DANGEROUS-INNERHTML", re.compile(r"\bdangerouslySetInnerHTML\b"), "React dangerouslySetInnerHTML usage"),
    ("TS-EVAL", re.compile(r"(?<![A-Za-z0-9_$])eval\s*\("), "Dynamic JavaScript eval() usage"),
    ("TS-FUNCTION-CONSTRUCTOR", re.compile(r"\bnew\s+Function\s*\("), "Dynamic Function constructor usage"),
    ("TS-DOCUMENT-WRITE", re.compile(r"\bdocument\.write\s*\("), "document.write() usage"),
)


def scan_python(path: Path) -> list[Finding]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except (SyntaxError, UnicodeDecodeError) as exc:
        return [Finding("PY-PARSE", "HIGH", str(path.relative_to(ROOT)), getattr(exc, "lineno", 1) or 1, str(exc))]
    visitor = PythonVisitor(path)
    visitor.visit(tree)
    return visitor.findings


def scan_typescript(path: Path) -> list[Finding]:
    text = path.read_text(encoding="utf-8")
    findings: list[Finding] = []
    for rule_id, pattern, message in _TS_RULES:
        for match in pattern.finditer(text):
            line = text.count("\n", 0, match.start()) + 1
            findings.append(Finding(rule_id, "HIGH", str(path.relative_to(ROOT)), line, message))
    return findings


def scan(root: Path = ROOT) -> dict:
    findings: list[Finding] = []
    scanned = 0
    for source_root in SOURCE_ROOTS:
        if not source_root.exists():
            continue
        for path in sorted(source_root.rglob("*")):
            if not path.is_file() or path.name in EXCLUDED_NAMES:
                continue
            if any(part in {"node_modules", "dist", "build", "__pycache__"} for part in path.parts):
                continue
            if path.suffix == ".py":
                scanned += 1
                findings.extend(scan_python(path))
            elif path.suffix in {".ts", ".tsx", ".js", ".jsx"}:
                scanned += 1
                findings.extend(scan_typescript(path))
    critical = [item for item in findings if item.severity in {"HIGH", "CRITICAL"}]
    return {
        "scanner": "crypto-trading-platform-local-sast",
        "classification": "LOCAL_STATIC_ANALYSIS_NOT_BANDIT_OR_SEMGREP",
        "scanned_files": scanned,
        "finding_count": len(findings),
        "high_or_critical_count": len(critical),
        "findings": [asdict(item) for item in findings],
    }


def main() -> int:
    report = scan(ROOT)
    out = ROOT / "reports" / "LOCAL_SAST.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        f"LOCAL_SAST scanned={report['scanned_files']} findings={report['finding_count']} "
        f"high_or_critical={report['high_or_critical_count']} classification={report['classification']}"
    )
    return 1 if report["high_or_critical_count"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
