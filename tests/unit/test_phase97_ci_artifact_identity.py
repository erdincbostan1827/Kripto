from __future__ import annotations

import subprocess
from pathlib import Path

import scripts.ci_artifact_identity as mod


def _repo(root: Path) -> str:
    subprocess.run(['git','init','-q'], cwd=root, check=True)
    subprocess.run(['git','config','user.email','t@example.invalid'], cwd=root, check=True)
    subprocess.run(['git','config','user.name','T'], cwd=root, check=True)
    (root/'seed').write_text('x')
    subprocess.run(['git','add','.'], cwd=root, check=True)
    subprocess.run(['git','commit','-q','-m','seed'], cwd=root, check=True)
    return subprocess.check_output(['git','rev-parse','HEAD'], cwd=root, text=True).strip()


def test_ci_artifact_identity_binds_digest_id_git_and_manifest(tmp_path: Path):
    sha = _repo(tmp_path)
    manifest = tmp_path/'reports/CI_BUILD_EVIDENCE_MANIFEST.json'
    manifest.parent.mkdir(parents=True)
    manifest.write_text('{}')
    out=tmp_path/'reports/CI_BUILD_ARTIFACT_IDENTITY.json'
    result=mod.bind(
        artifact_id='12345',
        artifact_digest='a'*64,
        artifact_name=f'ci-build-evidence-{sha}',
        expected_git_sha=sha,
        root=tmp_path,
        output=out,
    )
    assert result['verified'], result['problems']
    assert result['build_evidence_manifest_sha256'] == mod.sha256_file(manifest)


def test_ci_artifact_identity_rejects_bad_digest_and_name(tmp_path: Path):
    sha = _repo(tmp_path)
    manifest = tmp_path/'reports/CI_BUILD_EVIDENCE_MANIFEST.json'
    manifest.parent.mkdir(parents=True)
    manifest.write_text('{}')
    result=mod.bind(
        artifact_id='0',
        artifact_digest='not-a-digest',
        artifact_name='wrong',
        expected_git_sha=sha,
        root=tmp_path,
        output=tmp_path/'reports/out.json',
    )
    assert not result['verified']
    assert 'CI_ARTIFACT_ID_INVALID' in result['problems']
    assert 'CI_ARTIFACT_DIGEST_INVALID' in result['problems']
    assert 'CI_ARTIFACT_NAME_NOT_BOUND_TO_GIT' in result['problems']


def test_workflow_exports_and_binds_artifact_identity():
    root=Path(__file__).resolve().parents[2]
    text=(root/'.github/workflows/production-acceptance.yml').read_text()
    assert 'build_artifact_id: ${{ steps.upload_build_evidence.outputs.artifact-id }}' in text
    assert 'build_artifact_digest: ${{ steps.upload_build_evidence.outputs.artifact-digest }}' in text
    assert 'python scripts/ci_artifact_identity.py' in text
