from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path

import scripts.external.build_campaign_evidence_bundle as builder
from scripts.external.stage_campaign_evidence_bundle import verify_and_stage


ROOT = Path(__file__).resolve().parents[1]
WRAPPER = ROOT / "tools" / "run_phase252_atomic_campaign_handoff.ps1"
WORKFLOW = ROOT / ".github" / "workflows" / "phase252-atomic-campaign-handoff-syntax.yml"


def _sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _fixture(root: Path, *, candidate: str, env_id: str, topology: str) -> str:
    source = root / "reports/external_acceptance/campaign/source/events.jsonl"
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_bytes(b'{"event":"real-evidence-placeholder-fixture"}\n')
    source_rel = source.relative_to(root).as_posix()
    source_sha = _sha_bytes(source.read_bytes())

    challenge = root / "reports/external_acceptance/release_challenge.json"
    _write_json(
        challenge,
        {
            "schema_version": "2.3",
            "classification": "EXTERNAL_ACCEPTANCE_RELEASE_CHALLENGE",
            "challenge_id": "0123456789abcdef0123456789abcdef",
            "git_commit_sha": candidate,
        },
    )
    challenge_sha = _sha_bytes(challenge.read_bytes())
    env_hash = hashlib.sha256(env_id.encode()).hexdigest()
    classifications = {
        "private_stream.json": "CREDENTIALED_PRIVATE_STREAM_ACCEPTANCE",
        "paper_campaign.json": "REAL_MARKET_PAPER_CAMPAIGN_ACCEPTANCE",
        "live_shadow.json": "LIVE_SHADOW_CAMPAIGN_ACCEPTANCE",
        "profitability.json": "REAL_PIT_PROFITABILITY_ACCEPTANCE",
    }
    for name, classification in classifications.items():
        _write_json(
            root / "reports/external_acceptance/campaign" / name,
            {
                "schema_version": "1.0",
                "classification": classification,
                "real_system": True,
                "executed": True,
                "git_commit_sha": candidate,
                "release_challenge": {
                    "challenge_id": "0123456789abcdef0123456789abcdef",
                    "sha256": challenge_sha,
                },
                "environment": {
                    "acceptance_environment_id_hash": env_hash,
                    "topology_hash": topology,
                },
                "source_artifacts": [{"path": source_rel, "sha256": source_sha}],
            },
        )
    return source_rel


def test_builder_produces_phase251_compatible_exact_sha_bundle(tmp_path: Path, monkeypatch) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    candidate = "a" * 40
    env_id = "campaign-env-phase252"
    topology = "b" * 64
    _fixture(repo, candidate=candidate, env_id=env_id, topology=topology)
    monkeypatch.setattr(builder, "_git_sha", lambda root: candidate)

    output = tmp_path / "handoff" / "campaign.zip"
    result = builder.build_bundle(
        root=repo,
        candidate=candidate,
        acceptance_environment_id=env_id,
        topology_hash=topology,
        output=output,
    )

    assert result["verified"] is True
    assert result["classification"] == "PHASE252_CAMPAIGN_BUNDLE_BUILD_RECEIPT"
    assert result["atomic_publish"] is True
    assert result["candidate_sha"] == candidate
    assert result["bundle_sha256"] == _sha_bytes(output.read_bytes())
    assert result["live_enabled"] is False
    assert result["production_ready"] is False

    staging = tmp_path / "staged"
    staging.mkdir()
    transfer = verify_and_stage(
        output.resolve(),
        expected_sha256=result["bundle_sha256"],
        expected_candidate=candidate,
        root=staging,
    )
    assert transfer["verified"] is True
    assert transfer["candidate_sha"] == candidate
    assert transfer["acceptance_environment_id"] == env_id
    assert transfer["topology_hash"] == topology


def test_builder_detects_source_tamper_and_publishes_nothing(tmp_path: Path, monkeypatch) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    candidate = "c" * 40
    env_id = "campaign-env-phase252"
    topology = "d" * 64
    source_rel = _fixture(repo, candidate=candidate, env_id=env_id, topology=topology)
    monkeypatch.setattr(builder, "_git_sha", lambda root: candidate)
    (repo / source_rel).write_bytes(b"tampered\n")

    output = tmp_path / "handoff" / "campaign.zip"
    result = builder.build_bundle(
        root=repo,
        candidate=candidate,
        acceptance_environment_id=env_id,
        topology_hash=topology,
        output=output,
    )
    assert result["verified"] is False
    assert any("CAMPAIGN_SOURCE_ARTIFACT_HASH_MISMATCH" in p for p in result["problems"])
    assert not output.exists()


def test_builder_refuses_overwrite_and_repository_local_output(tmp_path: Path, monkeypatch) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    candidate = "e" * 40
    env_id = "campaign-env-phase252"
    topology = "f" * 64
    _fixture(repo, candidate=candidate, env_id=env_id, topology=topology)
    monkeypatch.setattr(builder, "_git_sha", lambda root: candidate)

    existing = tmp_path / "campaign.zip"
    existing.write_bytes(b"sentinel")
    overwrite = builder.build_bundle(
        root=repo,
        candidate=candidate,
        acceptance_environment_id=env_id,
        topology_hash=topology,
        output=existing,
    )
    assert overwrite["verified"] is False
    assert "OUTPUT_ALREADY_EXISTS" in overwrite["problems"]
    assert existing.read_bytes() == b"sentinel"

    inside = repo / "campaign.zip"
    local = builder.build_bundle(
        root=repo,
        candidate=candidate,
        acceptance_environment_id=env_id,
        topology_hash=topology,
        output=inside,
    )
    assert local["verified"] is False
    assert "OUTPUT_MUST_BE_OUTSIDE_REPOSITORY" in local["problems"]
    assert not inside.exists()


def test_builder_archive_is_deterministic_and_contains_only_bound_evidence(tmp_path: Path, monkeypatch) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    candidate = "1" * 40
    env_id = "campaign-env-phase252"
    topology = "2" * 64
    _fixture(repo, candidate=candidate, env_id=env_id, topology=topology)
    monkeypatch.setattr(builder, "_git_sha", lambda root: candidate)
    first = tmp_path / "first.zip"
    second = tmp_path / "second.zip"
    r1 = builder.build_bundle(root=repo, candidate=candidate, acceptance_environment_id=env_id, topology_hash=topology, output=first)
    r2 = builder.build_bundle(root=repo, candidate=candidate, acceptance_environment_id=env_id, topology_hash=topology, output=second)
    assert r1["verified"] is True and r2["verified"] is True
    assert first.read_bytes() == second.read_bytes()
    with zipfile.ZipFile(first) as archive:
        manifest = json.loads(archive.read("CAMPAIGN_BUNDLE_MANIFEST.json"))
        assert manifest["candidate_sha"] == candidate
        assert set(manifest["files"]) == set(archive.namelist()) - {"CAMPAIGN_BUNDLE_MANIFEST.json"}
        assert all(name.startswith("reports/external_acceptance/") for name in manifest["files"])


def test_phase252_wrapper_is_exact_head_toc_tou_safe_and_stops_at_paper_boundary() -> None:
    text = WRAPPER.read_text(encoding="utf-8")
    required = (
        "FINAL_ACCEPTANCE_REQUIRES_CURRENT_REMOTE_MAIN",
        "PHASE252_LOCAL_HEAD_NOT_CANDIDATE",
        "scripts/external/build_campaign_evidence_bundle.py",
        "PHASE252_CAMPAIGN_BUNDLE_BUILD_RECEIPT",
        "Get-FileHash -LiteralPath $bundlePath -Algorithm SHA256",
        "run_phase251_final_production_acceptance.ps1",
        "BUNDLE_CHANGED_DURING_PHASE251",
        "REMOTE_MAIN_MOVED_DURING_HANDOFF",
        "PHASE252_ATOMIC_CAMPAIGN_HANDOFF=PASS",
        "live_enabled = $false",
        'default_mode = "PAPER"',
    )
    for marker in required:
        assert marker in text
    assert "Remove-Item -LiteralPath $bundlePath" not in text


def test_phase252_windows_syntax_gate_is_pinned_and_runs_contract_tests() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")
    for marker in (
        "name: Phase 252 Atomic Campaign Handoff Syntax",
        "runs-on: windows-latest",
        "PYTHON_VERSION: '3.12.10'",
        "PYTEST_VERSION: '9.0.3'",
        "run_phase252_atomic_campaign_handoff.ps1",
        "build_campaign_evidence_bundle.py",
        "python -m py_compile scripts/external/build_campaign_evidence_bundle.py",
        "python -m pytest -q tests/test_phase252_atomic_campaign_handoff.py",
    ):
        assert marker in text
