from __future__ import annotations

from pathlib import Path

from scripts.external_acceptance_runner import build_plan
import scripts.external_acceptance_preflight as preflight
from scripts.verify_external_acceptance import GROUP_KEYS


def test_real_target_supply_chain_profile_only_verifies_transferred_ci_evidence():
    plan = build_plan("supply-chain")
    assert plan == [("transferred_supply_chain_verification", ["python", "scripts/external/verify_transferred_supply_chain.py"], True)]
    forbidden = {"gitleaks", "trivy", "syft", "pip-audit", "bandit", "semgrep", "pip-licenses"}
    assert not any(cmd and cmd[0] in forbidden for _, cmd, _ in plan)
    assert GROUP_KEYS["supply_chain"] == ("transferred_supply_chain_verification",)


def test_preflight_does_not_require_duplicate_scanner_binaries(monkeypatch):
    monkeypatch.setenv("PROVENANCE_SIGN_VERIFY_COMMAND", "approved-sign-and-verify")
    payload = preflight.evaluate()
    keys = {row["key"] for row in payload["checks"]}
    for tool in ("gitleaks", "trivy", "syft", "pip-audit", "bandit", "semgrep", "pip-licenses", "cosign"):
        assert f"tool:{tool}" not in keys
    assert payload["groups"]["signing_tooling"] is True


def test_production_workflow_build_job_retains_digest_pinned_scans():
    root = Path(__file__).resolve().parents[2]
    text = (root / ".github/workflows/production-acceptance.yml").read_text()
    assert '"$GITLEAKS_DIGEST" detect' in text
    assert '"$TRIVY_DIGEST" fs' in text
    assert '"$SYFT_DIGEST" dir:/repo' in text
    assert "verify_transferred_supply_chain.py" not in text  # orchestrator owns real-target verification


def test_external_verifier_contains_nested_transferred_supply_chain_semantic_check():
    root = Path(__file__).resolve().parents[2]
    text = (root / "scripts/verify_external_acceptance.py").read_text()
    assert 'TRANSFERRED_CI_SUPPLY_CHAIN_ACCEPTANCE' in text
    assert 'SUPPLY_CHAIN_SUBARTIFACT_INVALID' in text
    assert 'receipt.get("git_commit_sha") != expected_git' in text
