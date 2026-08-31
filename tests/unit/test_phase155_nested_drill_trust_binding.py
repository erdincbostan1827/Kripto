from pathlib import Path

def test_drill_evidence_requires_external_challenge_trust():
    text = Path("backend/app/release/drill_evidence.py").read_text()
    assert "verify_challenge(challenge_path, root=root, require_trust=True)" in text
    assert "require_trust=False" not in text

def test_restart_evidence_requires_external_challenge_trust():
    text = Path("backend/app/release/runtime_restart_evidence.py").read_text()
    assert "require_trust=True" in text
