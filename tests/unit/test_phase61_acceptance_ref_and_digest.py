from pathlib import Path
import subprocess
import tempfile
import pytest
import sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'scripts'))
from validate_acceptance_ref import validate

def test_current_annotated_tag_is_accepted(monkeypatch):
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp)
        subprocess.run(['git', 'init', '-q'], cwd=repo, check=True)
        subprocess.run(['git', 'config', 'user.name', 'Acceptance Test'], cwd=repo, check=True)
        subprocess.run(['git', 'config', 'user.email', 'acceptance-test@example.invalid'], cwd=repo, check=True)
        (repo / 'candidate.txt').write_text('candidate\n', encoding='utf-8')
        subprocess.run(['git', 'add', 'candidate.txt'], cwd=repo, check=True)
        subprocess.run(['git', 'commit', '-q', '-m', 'candidate'], cwd=repo, check=True)
        subprocess.run(['git', 'tag', '-a', 'acceptance-test', '-m', 'acceptance candidate'], cwd=repo, check=True)
        monkeypatch.chdir(repo)
        d=validate('acceptance-test')
    assert d['status']=='PASS' and d['kind']=='ANNOTATED_TAG'

def test_branch_is_rejected(monkeypatch):
    monkeypatch.chdir(ROOT)
    with pytest.raises(ValueError): validate('master')

def test_workflow_verifies_immutable_container_digest():
    text=(ROOT/'.github/workflows/production-acceptance.yml').read_text()
    assert 'container_digest: ${{ steps.image_digest.outputs.container_digest }}' in text
    assert 'EXPECTED_CONTAINER_DIGEST: ${{ needs.ci-build-evidence.outputs.container_digest }}' in text
    assert "test \"$ACTUAL\" = \"$EXPECTED_CONTAINER_DIGEST\"" in text

def test_workflow_enforces_acceptance_ref():
    text=(ROOT/'.github/workflows/production-acceptance.yml').read_text()
    assert 'validate_acceptance_ref.py "${{ github.event.inputs.acceptance_ref }}"' in text
