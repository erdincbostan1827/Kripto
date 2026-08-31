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
    subprocess.run(["git", "config", "user.email", "phase180@example.invalid"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.name", "Phase 180"], cwd=root, check=True)
    (root / "README.md").write_text("fixture\n", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=root, check=True)
    subprocess.run(["git", "commit", "-qm", "fixture"], cwd=root, check=True)
    return root


def _staged(root: Path, tmp_path: Path, files: dict[str, bytes], name: str = "staged") -> Path:
    staged = tmp_path / name
    staged.mkdir()
    rows = []
    for rel, data in files.items():
        path = staged / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        rows.append({"path": rel, "sha256": hashlib.sha256(data).hexdigest(), "size": len(data)})
    sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    manifest = {"source_git_commit_sha": sha, "file_count": len(rows), "files": rows}
    (staged / MANIFEST).write_text(json.dumps(manifest), encoding="utf-8")
    return staged


def _allow_semantics(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(promo, "_semantic_verify_candidate", lambda *a, **k: {"verified": True, "problems": [], "profiles": {}})
    monkeypatch.setattr(promo, "_post_promotion_verify", lambda *a, **k: {"verified": True, "problems": [], "profiles": {}, "release_gate_blockers": ["still fail-closed"], "release_gate_eligible": False})


def test_phase180_replay_ledger_blocks_second_promotion(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    root = _repo(tmp_path)
    old = root / "reports/external_acceptance/manifest_runtime.json"
    old.write_text("old\n", encoding="utf-8")
    staged = _staged(root, tmp_path, {"reports/external_acceptance/manifest_runtime.json": b"new\n"})
    _allow_semantics(monkeypatch)
    sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()

    first = promo.promote(staged, root=root, confirm_source_sha=sha)
    assert first["promoted"] is True
    ledger = json.loads((root / promo.IMPORT_LEDGER).read_text(encoding="utf-8"))
    assert len(ledger["events"]) == 1
    assert ledger["events"][0]["bundle_manifest_sha256"] == first["bundle_manifest_sha256"]

    second = promo.promote(staged, root=root, confirm_source_sha=sha)
    assert second["promoted"] is False
    assert "RETURN_BUNDLE_REPLAY" in second["problems"]
    assert len(json.loads((root / promo.IMPORT_LEDGER).read_text())["events"]) == 1


def test_phase180_post_swap_failure_rolls_back_canonical_and_does_not_record_replay(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    root = _repo(tmp_path)
    canonical = root / "reports/external_acceptance/manifest_runtime.json"
    canonical.write_text("old\n", encoding="utf-8")
    staged = _staged(root, tmp_path, {"reports/external_acceptance/manifest_runtime.json": b"new\n"})
    monkeypatch.setattr(promo, "_semantic_verify_candidate", lambda *a, **k: {"verified": True, "problems": [], "profiles": {}})
    monkeypatch.setattr(promo, "_post_promotion_verify", lambda *a, **k: {"verified": False, "problems": ["POST_PROMOTION_SEMANTIC_INVALID:fixture"], "profiles": {}})
    sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()

    result = promo.promote(staged, root=root, confirm_source_sha=sha)
    assert result["promoted"] is False
    assert result["rolled_back"] is True
    assert canonical.read_text(encoding="utf-8") == "old\n"
    assert not (root / promo.IMPORT_LEDGER).exists()


def test_phase180_ledger_failure_rolls_back_and_removes_new_lock_quarantine(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    root = _repo(tmp_path)
    canonical = root / "reports/external_acceptance/manifest_runtime.json"
    canonical.write_text("old\n", encoding="utf-8")
    staged = _staged(root, tmp_path, {
        "reports/external_acceptance/manifest_runtime.json": b"new\n",
        "uv.lock": b"version = 1\n",
        "frontend/package-lock.json": b'{"lockfileVersion":3}\n',
        promo.LOCK_PROMOTION_MANIFEST: b"{}\n",
    })
    _allow_semantics(monkeypatch)
    monkeypatch.setattr(promo, "_append_import_ledger", lambda *a, **k: (_ for _ in ()).throw(OSError("disk full")))
    sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()

    result = promo.promote(staged, root=root, confirm_source_sha=sha)
    assert result["promoted"] is False
    assert result["rolled_back"] is True
    assert canonical.read_text(encoding="utf-8") == "old\n"
    candidate = root / "reports/lock-promotion/candidates" / result["bundle_manifest_sha256"]
    assert not candidate.exists()


def test_phase180_import_ledger_is_hash_chained_and_tamper_fails_closed(tmp_path: Path):
    root = _repo(tmp_path)
    path = promo._append_import_ledger(root, bundle_manifest_sha256="1" * 64, source_git_commit_sha="2" * 40, promoted_files=["reports/external_acceptance/a.json"], artifact_classes=["CANONICAL_EXTERNAL_ACCEPTANCE"])
    doc, problems = promo._load_import_ledger(root)
    assert problems == []
    assert doc["events"][0]["previous_event_hash"] == promo.ZERO_HASH
    assert len(doc["events"][0]["event_hash"]) == 64

    ledger_path = Path(path)
    tampered = json.loads(ledger_path.read_text())
    tampered["events"][0]["promoted_files"] = ["reports/external_acceptance/tampered.json"]
    ledger_path.write_text(json.dumps(tampered), encoding="utf-8")
    _, problems = promo._load_import_ledger(root)
    assert "IMPORT_LEDGER_HASH_INVALID:0" in problems


def test_phase180_unified_import_contract_classifies_browser_supply_chain_and_locks():
    classes = promo._artifact_classes([
        "reports/external_acceptance/manifest_frontend.json",
        "reports/external_acceptance/sbom.cdx.json",
        "reports/external_acceptance/provenance.json",
        "uv.lock",
        "frontend/package-lock.json",
        promo.LOCK_PROMOTION_MANIFEST,
    ])
    assert classes == sorted({
        "CANONICAL_EXTERNAL_ACCEPTANCE",
        "DEPENDENCY_LOCK_CANDIDATE",
        "FRONTEND_BROWSER_EVIDENCE",
        "SUPPLY_CHAIN_EVIDENCE",
    })
