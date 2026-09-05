from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FINAL_MAIN_WORKFLOWS = (
    ".github/workflows/phase224-hosted-evidence.yml",
    ".github/workflows/phase225-production-build-evidence.yml",
    ".github/workflows/phase265-campaign-collector-contract.yml",
    ".github/workflows/phase266-campaign-runtime-contract.yml",
)


def _push_block(path: str) -> str:
    text = (ROOT / path).read_text(encoding="utf-8")
    assert "\non:\n" in text
    assert "\n  push:\n" in text
    assert "\n  pull_request:\n" in text
    return text.split("\n  push:\n", 1)[1].split("\n  pull_request:\n", 1)[0]


def test_phase262_required_gates_are_not_path_filtered_on_push() -> None:
    for workflow in REQUIRED_FINAL_MAIN_WORKFLOWS:
        push = _push_block(workflow)
        assert "paths:" not in push, (
            f"{workflow} is required by the Phase262 exact-main dispatcher and "
            "must therefore produce a run for every applicable push."
        )


def test_main_scoped_required_gates_include_main() -> None:
    for workflow in REQUIRED_FINAL_MAIN_WORKFLOWS[:2] + REQUIRED_FINAL_MAIN_WORKFLOWS[3:]:
        push = _push_block(workflow)
        assert "- main" in push


def test_phase262_dispatcher_still_requires_all_liveness_gates() -> None:
    dispatcher = (ROOT / ".github/workflows/phase262-final-main-phase245-dispatch.yml").read_text(
        encoding="utf-8"
    )
    required_names = (
        "Phase 224 Hosted Pre-Acceptance Evidence",
        "Phase 225 Production Build Evidence",
        "Phase265 Campaign Collector Contract",
        "Phase266 Campaign Runtime Contract",
    )
    for name in required_names:
        assert f'"{name}"' in dispatcher


def test_truth_boundary_phrase_remains_present() -> None:
    dispatcher = (ROOT / ".github/workflows/phase262-final-main-phase245-dispatch.yml").read_text(
        encoding="utf-8"
    )
    assert "Dispatch success is not Phase245 acceptance evidence" in dispatcher
