from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PHASE265 = ROOT / "scripts/external/phase265_campaign_collector.py"
LEGACY = ROOT / "scripts/external/record_campaign_evidence.py"


def _run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=30,
        check=False,
    )


def test_phase265_cli_names_untrusted_sources_as_audit_only() -> None:
    result = _run(str(PHASE265), "--help")
    assert result.returncode == 0, result.stderr
    output = result.stdout
    assert "collect-market-audit" in output
    assert "ingest-audit" in output
    assert "kill-switch-audit" in output
    assert "collect-shadow" not in output
    assert " ingest " not in f" {output} "


def test_legacy_arbitrary_append_is_fail_closed() -> None:
    result = _run(
        str(LEGACY),
        "append",
        "--kind",
        "paper_sample",
        "--payload-file",
        "does-not-matter.json",
    )
    assert result.returncode == 1
    assert "legacy recorder is audit-only" in result.stdout.lower()
    assert '"production_ready": false' in result.stdout.lower()
    assert '"live_enabled": false' in result.stdout.lower()


def test_legacy_finalize_is_fail_closed() -> None:
    result = _run(str(LEGACY), "finalize")
    assert result.returncode == 1
    assert "protected-runtime hmac-attested telemetry" in result.stdout.lower()
    assert '"production_ready": false' in result.stdout.lower()
    assert '"live_enabled": false' in result.stdout.lower()
