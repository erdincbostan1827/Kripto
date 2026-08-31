from pathlib import Path
import subprocess
import tempfile
import pytest
import sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'scripts'))
from validate_acceptance_ref import validate

def test_current_annotated_tag_is_accepted(monkeypatch):
    monkeypatch.chdir(ROOT)
    tag = subprocess.check_output(['git','tag','--points-at','HEAD'], text=True).splitlines()[0]
    d=validate(tag)
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
