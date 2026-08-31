from pathlib import Path

from scripts.verify_workflow_action_pins import verify_workflow_action_pins


def test_repository_workflow_actions_are_immutable_sha_pinned():
    result = verify_workflow_action_pins()
    assert result["verified"], result["problems"]
    assert result["checked_action_count"] >= 10


def test_moving_major_tag_is_rejected(tmp_path: Path):
    wf = tmp_path / ".github/workflows/ci.yml"
    wf.parent.mkdir(parents=True)
    wf.write_text("jobs:\n  t:\n    steps:\n      - uses: actions/checkout@v4\n", encoding="utf-8")
    result = verify_workflow_action_pins(tmp_path)
    assert not result["verified"]
    assert any("UNPINNED_ACTION" in p for p in result["problems"])


def test_subpath_sha_action_is_accepted_and_mutable_container_action_is_rejected(tmp_path: Path):
    wf = tmp_path / ".github/workflows/ci.yml"
    wf.parent.mkdir(parents=True)
    wf.write_text(
        "jobs:\n  t:\n    steps:\n"
        "      - uses: owner/repo/sub/action@" + "a"*40 + "\n"
        "      - uses: docker://example/tool:latest\n",
        encoding="utf-8",
    )
    result = verify_workflow_action_pins(tmp_path)
    assert not result["verified"]
    assert not any("owner/repo/sub/action" in p for p in result["problems"])
    assert any("UNPINNED_CONTAINER_ACTION" in p for p in result["problems"])
