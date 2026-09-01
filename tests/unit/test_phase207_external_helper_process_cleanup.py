from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

import scripts.trusted_signing_adapter as signing
import scripts.external.frontend_browser_acceptance as frontend
import scripts.external.tauri_build_readiness as tauri


def test_trusted_verifier_timeout_from_bounded_runner_fails_closed(monkeypatch, tmp_path: Path):
    env = tmp_path / "envelope.json"
    env.write_text('{"classification":"TRUSTED_SIGNING_ENVELOPE"}', encoding="utf-8")

    # Reach only the runner contract by replacing the pre-run validation inputs.
    monkeypatch.setattr(signing, "_sha", lambda p: "a" * 64)
    monkeypatch.setattr(signing.json, "loads", lambda text: {
        "classification": "TRUSTED_SIGNING_ENVELOPE",
        "signature_status": "SIGNED_EXTERNAL_UNVERIFIED",
        "nonce": "n" * 64,
        "issued_at": "2026-09-01T10:00:00+00:00",
        "expires_at": "2026-09-01T10:05:00+00:00",
        "subject_sha256": "b" * 64,
        "canonical_payload_sha256": "c" * 64,
        "signing_identity": "ci-key://phase207",
    })
    class FixedDateTime(signing.datetime):
        @classmethod
        def now(cls, tz=None):
            return cls.fromisoformat("2026-09-01T10:01:00+00:00")
    monkeypatch.setattr(signing, "datetime", FixedDateTime)

    def timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired(args[0], kwargs["timeout"], output="partial", stderr="err")
    monkeypatch.setattr(signing, "run_captured_split", timeout)

    out = tmp_path / "receipt.json"
    with pytest.raises(RuntimeError, match="TRUSTED_SIGNATURE_VERIFIER_TIMEOUT"):
        signing.verify_external_signature(
            envelope=env,
            verifier_command=[sys.executable, "verifier.py"],
            verifier_identity="trusted://phase207",
            output=out,
            timeout_seconds=1,
        )
    assert not out.exists()


def test_frontend_external_command_timeout_is_blocked(monkeypatch, tmp_path: Path):
    monkeypatch.setattr(frontend.shutil, "which", lambda tool: f"/fake/{tool}")
    def timeout(command, *, cwd, timeout, env=None):
        raise subprocess.TimeoutExpired(command, timeout, output="partial")
    monkeypatch.setattr(frontend, "run_captured", timeout)
    row = frontend._run(["npm", "ci"], cwd=tmp_path, timeout=1)
    assert row["status"] == "BLOCKED"
    assert row["blocker"] == "TIMEOUT"
    assert "partial" in row["output"]


def test_tauri_external_command_timeout_is_blocked(monkeypatch, tmp_path: Path):
    monkeypatch.setattr(tauri.shutil, "which", lambda tool: f"/fake/{tool}")
    def timeout(command, *, cwd, timeout, env=None):
        raise subprocess.TimeoutExpired(command, timeout, output="partial")
    monkeypatch.setattr(tauri, "run_captured", timeout)
    row = tauri.run_cmd(["cargo", "build"], tmp_path, 1)
    assert row["status"] == "BLOCKED"
    assert row["blocker"] == "TIMEOUT"
