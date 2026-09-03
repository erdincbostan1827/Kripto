from __future__ import annotations

import json
import os
from pathlib import Path

import scripts.external.ledger_checkpoint_sign_verify as signer
import scripts.external.verify_ledger_checkpoint as verifier


ROOT = Path(__file__).resolve().parents[1]
ORCHESTRATOR = ROOT / "scripts" / "production_acceptance_orchestrator.py"
VERIFY_SCRIPT = ROOT / "scripts" / "external" / "verify_ledger_checkpoint.py"
SIGN_SCRIPT = ROOT / "scripts" / "external" / "ledger_checkpoint_sign_verify.py"


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_phase247_final_orchestrator_uses_python_ledger_entrypoint() -> None:
    text = _text(ORCHESTRATOR)
    assert '[sys.executable, "scripts/external/ledger_checkpoint_sign_verify.py"]' in text
    assert '["bash", "scripts/external/ledger_checkpoint_sign_verify.sh"]' not in text


def test_phase247_ledger_scripts_reuse_hardened_cross_platform_launcher() -> None:
    verify_text = _text(VERIFY_SCRIPT)
    sign_text = _text(SIGN_SCRIPT)
    assert "from scripts.external.run_approved_drill import _run_redacted, _shell_argv" in verify_text
    assert "from scripts.external.run_approved_drill import _required_env, _run_redacted, _shell_argv" in sign_text
    assert "shell=True" not in verify_text
    assert "shell=True" not in sign_text
    assert '["bash", "-lc"' not in verify_text
    assert '["bash", "-lc"' not in sign_text


def test_ledger_verifier_fails_closed_without_external_trust(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(verifier, "ROOT", tmp_path)
    monkeypatch.setattr(
        verifier,
        "verify_ledger_checkpoint",
        lambda *args, **kwargs: {
            "verified": True,
            "problems": [],
            "trust_status": "NOT_CONFIGURED",
            "trust_verified": False,
        },
    )
    monkeypatch.delenv(verifier.TRUST_ENV, raising=False)

    result = verifier.verify_with_external_trust(tmp_path / "checkpoint.json")

    assert result["verified"] is False
    assert result["trust_verified"] is False
    assert "LEDGER_CHECKPOINT_EXTERNAL_TRUST_VERIFIER_MISSING" in result["problems"]


def test_ledger_verifier_runs_external_trust_with_bound_paths(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(verifier, "ROOT", tmp_path)
    checkpoint = tmp_path / "reports" / "external_acceptance" / "evidence_ledger_checkpoint.json"
    signature = tmp_path / "reports" / "external_acceptance" / "checkpoint.sig"
    checkpoint.parent.mkdir(parents=True)
    signature.write_text("signature", encoding="utf-8")
    checkpoint.write_text(
        json.dumps({"signature_artifact": "reports/external_acceptance/checkpoint.sig"}) + "\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        verifier,
        "verify_ledger_checkpoint",
        lambda *args, **kwargs: {
            "verified": True,
            "problems": [],
            "trust_status": "NOT_CONFIGURED",
            "trust_verified": False,
        },
    )
    monkeypatch.setenv(verifier.TRUST_ENV, "opaque trust command")
    monkeypatch.setenv("ACCEPTANCE_ENVIRONMENT_ID", "env-1")
    monkeypatch.setenv("ACCEPTANCE_TOPOLOGY_HASH", "a" * 64)
    observed: dict[str, str] = {}

    def fake_shell(command: str) -> list[str]:
        assert command == "opaque trust command"
        return ["powershell", "-Command", command]

    def fake_run(argv: list[str], *, secret_command: str | None = None) -> int:
        assert argv[0] == "powershell"
        assert secret_command == "opaque trust command"
        observed["checkpoint"] = os.environ["ACCEPTANCE_LEDGER_CHECKPOINT_PATH"]
        observed["ledger"] = os.environ["ACCEPTANCE_LEDGER_PATH"]
        observed["signature"] = os.environ["ACCEPTANCE_LEDGER_CHECKPOINT_SIGNATURE_PATH"]
        return 0

    monkeypatch.setattr(verifier, "_shell_argv", fake_shell)
    monkeypatch.setattr(verifier, "_run_redacted", fake_run)

    result = verifier.verify_with_external_trust(checkpoint)

    assert result["verified"] is True
    assert result["trust_verified"] is True
    assert result["trust_status"] == "VERIFIED_BY_EXTERNAL_COMMAND"
    assert observed["checkpoint"] == str(checkpoint.resolve())
    assert observed["ledger"] == str((tmp_path / verifier.LEDGER_PATH).resolve())
    assert observed["signature"] == str(signature.resolve())
    assert "ACCEPTANCE_LEDGER_CHECKPOINT_PATH" not in os.environ
    assert "ACCEPTANCE_LEDGER_PATH" not in os.environ
    assert "ACCEPTANCE_LEDGER_CHECKPOINT_SIGNATURE_PATH" not in os.environ


def test_ledger_sign_failure_prevents_checkpoint_verification(monkeypatch) -> None:
    monkeypatch.setattr(signer, "_required_env", lambda name: "opaque signing command")
    monkeypatch.setattr(signer, "_shell_argv", lambda command: ["powershell", "-Command", command])
    monkeypatch.setattr(signer, "_run_redacted", lambda argv, *, secret_command=None: 9)

    def should_not_verify(path: Path) -> dict:
        raise AssertionError("verification must not run after signing failure")

    monkeypatch.setattr(signer, "verify_with_external_trust", should_not_verify)
    assert signer.main() == 2
