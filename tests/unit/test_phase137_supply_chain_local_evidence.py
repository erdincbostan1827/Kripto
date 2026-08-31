from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_local_sast_executes_and_has_no_high_or_critical_findings() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/local_sast.py"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
        timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    report = json.loads((ROOT / "reports/LOCAL_SAST.json").read_text(encoding="utf-8"))
    assert report["classification"] == "LOCAL_STATIC_ANALYSIS_NOT_BANDIT_OR_SEMGREP"
    assert report["scanned_files"] > 0
    assert report["high_or_critical_count"] == 0


def test_local_sbom_is_cyclonedx_1_6_but_remains_direct_only() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/generate_local_sbom.py"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
        timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    sbom = json.loads((ROOT / "reports/SBOM.local.json").read_text(encoding="utf-8"))
    assert sbom["bomFormat"] == "CycloneDX"
    assert sbom["specVersion"] == "1.6"
    assert sbom["metadata"]["resolved_dependency_lock"] is False
    assert sbom["metadata"]["transitive_dependencies_resolved"] is False
    assert sbom["metadata"]["vulnerability_scan_performed"] is False


def test_local_sast_detects_known_python_and_frontend_probes() -> None:
    from scripts.local_sast import scan_python, scan_typescript

    py_probe = ROOT / "backend/.phase137_sast_probe.py"
    ts_probe = ROOT / "frontend/src/.phase137_sast_probe.tsx"
    try:
        py_probe.write_text(
            "import subprocess\n"
            "def unsafe(user):\n"
            "    eval(user)\n"
            "    subprocess.run(user, shell=True)\n",
            encoding="utf-8",
        )
        ts_probe.write_text(
            "export const Unsafe = () => <div dangerouslySetInnerHTML={{__html: 'x'}} />;\n",
            encoding="utf-8",
        )
        py_rules = {finding.rule_id for finding in scan_python(py_probe)}
        ts_rules = {finding.rule_id for finding in scan_typescript(ts_probe)}
        assert {"PY-EVAL-EXEC", "PY-SUBPROCESS-SHELL"} <= py_rules
        assert "TS-DANGEROUS-INNERHTML" in ts_rules
    finally:
        py_probe.unlink(missing_ok=True)
        ts_probe.unlink(missing_ok=True)
