from __future__ import annotations

import json
import subprocess
from pathlib import Path

import scripts.generate_release_manifest as release
from scripts.verify_local_coverage import verify


def _git(root: Path) -> str:
    subprocess.run(['git','init','-q'], cwd=root, check=True)
    subprocess.run(['git','config','user.email','t@example.invalid'], cwd=root, check=True)
    subprocess.run(['git','config','user.name','T'], cwd=root, check=True)
    (root/'seed').write_text('x')
    subprocess.run(['git','add','.'], cwd=root, check=True)
    subprocess.run(['git','commit','-q','-m','seed'], cwd=root, check=True)
    return subprocess.check_output(['git','rev-parse','HEAD'], cwd=root, text=True).strip()


def _coverage_tree(root: Path, sha: str) -> Path:
    d=root/'reports/local_coverage'; d.mkdir(parents=True)
    data=d/'.coverage.00_of_01'; data.write_bytes(b'data')
    shard=d/'coverage_shard_00_of_01.json'
    shard.write_text(json.dumps({
      'git_commit_sha':sha,'status':'PASS','exit_code':0,
      'coverage_data':'reports/local_coverage/.coverage.00_of_01',
      'coverage_data_sha256':__import__('hashlib').sha256(data.read_bytes()).hexdigest(),
    }))
    cov=d/'coverage.json'; cov.write_text(json.dumps({'totals':{'percent_covered':91.25}}))
    full=d/'full_coverage_manifest.json'
    full.write_text(json.dumps({
      'classification':'LOCAL_FULL_COVERAGE_EVIDENCE','git_commit_sha':sha,'status':'PASS','problems':[],
      'coverage_percent':91.25,'coverage_json':'reports/local_coverage/coverage.json',
      'coverage_json_sha256':__import__('hashlib').sha256(cov.read_bytes()).hexdigest(),
      'shard_count':1,'shards':[{'manifest':'reports/local_coverage/coverage_shard_00_of_01.json','manifest_sha256':__import__('hashlib').sha256(shard.read_bytes()).hexdigest()}],
    }))
    return full


def test_git_bound_coverage_verifier_accepts_complete_bound_tree(tmp_path: Path):
    sha=_git(tmp_path); full=_coverage_tree(tmp_path,sha)
    result=verify(full,root=tmp_path)
    assert result['verified'] and result['coverage_percent']==91.25


def test_git_bound_coverage_verifier_rejects_stale_git(tmp_path: Path):
    sha=_git(tmp_path); full=_coverage_tree(tmp_path,sha)
    (tmp_path/'new').write_text('y'); subprocess.run(['git','add','.'],cwd=tmp_path,check=True); subprocess.run(['git','commit','-q','-m','new'],cwd=tmp_path,check=True)
    result=verify(full,root=tmp_path)
    assert not result['verified'] and 'GIT_COMMIT_MISMATCH' in result['problems']


def test_release_coverage_truth_prefers_verified_machine_evidence(monkeypatch, tmp_path: Path):
    monkeypatch.setattr(release,'ROOT',tmp_path)
    sha=_git(tmp_path); _coverage_tree(tmp_path,sha)
    (tmp_path/'reports/LATEST_COVERAGE.txt').write_text('PRIOR VERIFIED REFERENCE\nTOTAL 100 7 93%\n')
    result=release.coverage_truth()
    assert result['fresh'] is True
    assert result['percent']==91.25
    assert result['classification']=='FRESH_GIT_BOUND_COVERAGE_EVIDENCE'


def test_coverage_cli_scripts_are_directly_invokable():
    root=Path(__file__).resolve().parents[2]
    for script,args in [
        ('scripts/local_coverage_runner.py',['--help']),
        ('scripts/merge_local_coverage.py',['--help']),
        ('scripts/verify_local_coverage.py',[]),
    ]:
        proc=subprocess.run(['python',script,*args],cwd=root,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        if script.endswith('verify_local_coverage.py'):
            assert proc.returncode in {0,2}
        else:
            assert proc.returncode==0, proc.stderr


def test_coverage_runner_cleans_stale_parallel_data(monkeypatch, tmp_path: Path):
    import scripts.local_coverage_runner as runner
    monkeypatch.setattr(runner,'ROOT',tmp_path)
    monkeypatch.setattr(runner,'REPORTS',tmp_path/'reports/local_coverage')
    monkeypatch.setattr(runner,'discover',lambda:['tests/test_x.py'])
    monkeypatch.setattr(runner,'_git_sha',lambda:'a'*40)
    runner.REPORTS.mkdir(parents=True)
    stale=runner.REPORTS/'.coverage.00_of_01.old'; stale.write_bytes(b'stale')
    class Proc:
        returncode=0; stdout='ok'
    def fake_run(command, **kwargs):
        data=runner.REPORTS/'.coverage.00_of_01.localhost.pid.new'
        data.write_bytes(b'fresh')
        return Proc()
    monkeypatch.setattr(runner,'run_captured',fake_run)
    payload=runner.run_shard(0,1,10)
    assert payload['status']=='PASS'
    assert not stale.exists()
    assert (runner.REPORTS/'.coverage.00_of_01').read_bytes()==b'fresh'
