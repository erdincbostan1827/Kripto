from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "phase262-final-main-phase245-dispatch.yml"


def test_phase262_final_main_router_waits_for_all_hosted_gates() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")
    for name in (
        "CI",
        "Phase 223 Chromium Browser Acceptance",
        "Phase 224 Hosted Pre-Acceptance Evidence",
        "Phase 225 Production Build Evidence",
        "Backend Full-Tree Type Debt Ratchet",
    ):
        assert name in text
    assert "PHASE262_FINAL_MAIN_GATES=PASS" in text
    assert 'conclusion" != "success"' in text


def test_phase262_final_main_router_dispatch_is_bounded_and_exact_sha() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "CANDIDATE_REF: ${{ github.sha }}" in text
    assert "phase245-binance-testnet-acceptance.yml" in text
    assert "-f symbol=AUTO" in text
    assert "-f max_notional=15" in text
    assert "-f partial_price=AUTO" in text
    assert "Dispatch success is not Phase245 acceptance evidence" in text
