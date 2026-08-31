from pathlib import Path


def test_merge_reverifies_release_challenge_with_trust_before_aggregate_pass():
    text = Path("scripts/merge_external_acceptance.py").read_text(encoding="utf-8")
    assert 'verify_challenge(reports / "release_challenge.json", root=root, require_trust=True)' in text
    assert 'MERGE_RELEASE_CHALLENGE_NOT_TRUSTED' in text
    assert 'challenge.get("trust_verified")' in text


def test_aggregate_ledger_append_requires_trusted_challenge():
    text = Path("scripts/merge_external_acceptance.py").read_text(encoding="utf-8")
    assert 'challenge.get("verified") and challenge.get("trust_verified")' in text
