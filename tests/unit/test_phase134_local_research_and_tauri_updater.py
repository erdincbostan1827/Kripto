from pathlib import Path
import json
import pytest

from app.research.final_evidence import build_local_fixture_evidence
from scripts.configure_tauri_updater import build_updater_fragment

ROOT = Path(__file__).resolve().parents[2]


def test_phase134_local_fixture_walk_forward_purged_embargo_cost_stress_and_effective_sample_are_real_code_paths():
    returns = [0.004, 0.003, -0.001, 0.005, 0.002, 0.003, -0.0005, 0.0045, 0.0025, 0.0035] * 8
    evidence = build_local_fixture_evidence(returns)
    assert evidence.classification == "LOCAL_FIXTURE_ONLY_NOT_PRODUCTION_PROFITABILITY_EVIDENCE"
    assert evidence.walk_forward_folds >= 2
    assert evidence.purged_embargo_no_overlap
    assert evidence.effective_sample_size >= 10
    assert set(evidence.cost_adverse_scenarios) == {
        "fee:adverse_fee", "slippage:adverse_slippage", "latency:adverse_latency",
        "funding:adverse_funding"
    }
    assert all(v > 0 for v in evidence.cost_adverse_scenarios.values())
    assert evidence.accepted_under_fixture_thresholds


def test_phase134_tauri_updater_configuration_is_signature_first_https_only_and_has_no_private_key():
    fake_public_material = "PUBLIC-KEY-CONTENT-ONLY-" + "A" * 48
    fragment = build_updater_fragment(
        public_key=fake_public_material,
        endpoint="https://updates.example.test/{{target}}/{{arch}}/{{current_version}}",
    )
    assert fragment["bundle"]["createUpdaterArtifacts"] is True
    cfg = fragment["plugins"]["updater"]
    assert cfg["pubkey"] == fake_public_material
    assert cfg["endpoints"][0].startswith("https://")
    assert cfg["dangerousInsecureTransportProtocol"] is False
    assert cfg["dangerousAcceptInvalidCerts"] is False
    assert cfg["dangerousAcceptInvalidHostnames"] is False
    combined = json.dumps(fragment).lower()
    assert "private_key" not in combined and "signing_private" not in combined


@pytest.mark.parametrize("endpoint", [
    "http://updates.example.test/latest.json",
    "https://user:pass@updates.example.test/latest.json",
    "file:///tmp/latest.json",
])
def test_phase134_tauri_updater_rejects_unsafe_release_endpoints(endpoint):
    with pytest.raises(ValueError):
        build_updater_fragment(public_key="K" * 64, endpoint=endpoint)


def test_phase134_tauri_shell_initializes_updater_plugin_but_real_build_and_signing_remain_unclaimed():
    cargo = (ROOT / "frontend/src-tauri/Cargo.toml").read_text(encoding="utf-8")
    main = (ROOT / "frontend/src-tauri/src/main.rs").read_text(encoding="utf-8")
    doc = (ROOT / "docs/TAURI_SIGNED_UPDATE.md").read_text(encoding="utf-8")
    assert 'tauri-plugin-updater = "=2.10.1"' in cargo
    assert "tauri_plugin_updater::Builder::new().build()" in main
    assert "No private signing key is stored" in doc
    assert "remain external acceptance requirements" in doc
