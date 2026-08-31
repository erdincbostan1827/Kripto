import scripts.external_acceptance_preflight as preflight


def test_preflight_requires_challenge_trust_and_provenance_signing(monkeypatch):
    monkeypatch.delenv("ACCEPTANCE_CHALLENGE_VERIFY_COMMAND", raising=False)
    monkeypatch.delenv("PROVENANCE_SIGN_VERIFY_COMMAND", raising=False)
    payload = preflight.evaluate()
    assert payload["groups"]["challenge_trust_contract"] is False
    assert payload["groups"]["provenance_sign_verify_contract"] is False
    keys = {row["key"] for row in payload["checks"]}
    assert "env:ACCEPTANCE_CHALLENGE_VERIFY_COMMAND" in keys
    assert "env:PROVENANCE_SIGN_VERIFY_COMMAND" in keys
    assert payload["all_external_prerequisites_ready"] is False


def test_preflight_redacts_command_values(monkeypatch):
    monkeypatch.setenv("ACCEPTANCE_CHALLENGE_VERIFY_COMMAND", "super-secret-command")
    monkeypatch.setenv("PROVENANCE_SIGN_VERIFY_COMMAND", "another-secret-command")
    payload = preflight.evaluate()
    rows = {row["key"]: row for row in payload["checks"]}
    assert rows["env:ACCEPTANCE_CHALLENGE_VERIFY_COMMAND"]["detail"] == "PRESENT_REDACTED"
    assert rows["env:PROVENANCE_SIGN_VERIFY_COMMAND"]["detail"] == "PRESENT_REDACTED"
    serialized = str(payload)
    assert "super-secret-command" not in serialized
    assert "another-secret-command" not in serialized
