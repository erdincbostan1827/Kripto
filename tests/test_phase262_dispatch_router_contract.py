from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "phase262-issue47-dispatch-router.yml"


def test_phase262_router_is_owner_issue_and_command_gated() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "github.event.issue.number == 47" in text
    assert "github.event.comment.user.login == 'erdincbostan1827'" in text
    assert "github.event.comment.body == '/phase245-final'" in text


def test_phase262_router_dispatches_only_bounded_testnet_parameters() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "phase245-binance-testnet-acceptance.yml" in text
    assert "-f symbol=AUTO" in text
    assert "-f max_notional=15" in text
    assert "-f partial_price=AUTO" in text
    assert "CANDIDATE_REF: ${{ github.sha }}" in text
    assert "Router success is not Phase245 acceptance evidence" in text
