from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

import pytest

import scripts.external.acceptance_return_promotion as promo
from scripts.external.acceptance_return_bundle import MANIFEST


def _repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    (root / "reports/external_acceptance").mkdir(parents=True)
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.email", "phase179@example.invalid"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.name", "Phase 179"], cwd=root, check=True)
    (root / "README.md").write_text("fixture\n")
    subprocess.run(["git", "add", "."], cwd=root, check=True)
    subprocess.run(["git", "commit", "-qm", "fixture"], cwd=root, check=True)
    return root


def _staged(root: Path, tmp_path: Path, files: dict[str, bytes]) -> Path:
    staged = tmp_path / "staged"; staged.mkdir()
    rows=[]
    for rel,data in files.items():
        p=staged/rel; p.parent.mkdir(parents=True,exist_ok=True); p.write_bytes(data)
        rows.append({"path":rel,"sha256":hashlib.sha256(data).hexdigest(),"size":len(data)})
    sha=subprocess.check_output(["git","rev-parse","HEAD"],cwd=root,text=True).strip()
    manifest={"source_git_commit_sha":sha,"file_count":len(rows),"files":rows}
    (staged/MANIFEST).write_text(json.dumps(manifest))
    return staged


def test_phase179_assess_rejects_partial_lock_set(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    root=_repo(tmp_path)
    staged=_staged(root,tmp_path,{"uv.lock":b"v=1\n"})
    result=promo.assess(staged,root=root)
    assert result["verified"] is False
    assert "LOCK_SET_PARTIAL" in result["problems"]
    assert result["locks_auto_promotable"] is False


def test_phase179_promote_requires_explicit_source_confirmation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    root=_repo(tmp_path)
    staged=_staged(root,tmp_path,{"reports/external_acceptance/evidence.txt":b"ok\n"})
    monkeypatch.setattr(promo,"_semantic_verify_candidate",lambda *a,**k:{"verified":True,"problems":[],"profiles":{}})
    result=promo.promote(staged,root=root,confirm_source_sha="f"*40)
    assert result["promoted"] is False
    assert "PROMOTION_SOURCE_CONFIRMATION_MISMATCH" in result["problems"]


def test_phase179_canonical_evidence_directory_transaction_and_lock_quarantine(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    root=_repo(tmp_path)
    canonical=root/"reports/external_acceptance/manifest_runtime.json"
    canonical.write_text("old\n")
    lock_manifest=b'{}\n'; uv=b"version = 1\n"; npm=b'{"lockfileVersion":3}\n'
    staged=_staged(root,tmp_path,{
        "reports/external_acceptance/manifest_runtime.json":b"new\n",
        "uv.lock":uv,"frontend/package-lock.json":npm,
        promo.LOCK_PROMOTION_MANIFEST:lock_manifest,
    })
    monkeypatch.setattr(promo,"_semantic_verify_candidate",lambda *a,**k:{"verified":True,"problems":[],"profiles":{}})
    sha=subprocess.check_output(["git","rev-parse","HEAD"],cwd=root,text=True).strip()
    result=promo.promote(staged,root=root,confirm_source_sha=sha)
    assert result["promoted"] is True
    assert canonical.read_text()=="new\n"
    assert not (root/"uv.lock").exists()
    assert not (root/"frontend/package-lock.json").exists()
    candidate=Path(result["lock_candidate_path"])
    assert (candidate/"uv.lock").read_bytes()==uv
    assert (candidate/"frontend/package-lock.json").read_bytes()==npm
    tx=json.loads((root/"reports/external_acceptance/PROMOTION_TRANSACTION.json").read_text())
    assert tx["classification"]==promo.PROMOTION_CLASSIFICATION


def test_phase179_staged_hash_tamper_fails_before_semantic_verification(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    root=_repo(tmp_path)
    staged=_staged(root,tmp_path,{"reports/external_acceptance/evidence.txt":b"ok\n"})
    (staged/"reports/external_acceptance/evidence.txt").write_text("tampered\n")
    called=False
    def semantic(*a,**k):
        nonlocal called; called=True; return {"verified":True,"problems":[],"profiles":{}}
    monkeypatch.setattr(promo,"_semantic_verify_candidate",semantic)
    result=promo.assess(staged,root=root)
    assert result["verified"] is False
    assert called is False
    assert any(p.startswith("STAGED_HASH_MISMATCH:") for p in result["problems"])
