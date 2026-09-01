from pathlib import Path

from scripts.local_load_soak import run_load_soak

ROOT = Path(__file__).resolve().parents[2]


def test_phase128_local_mock_soak_has_bounded_retained_memory_growth():
    result = run_load_soak(
        duplicate_submits=500, event_messages=500, mtf_cycles=8, memory_cycles=24,
        retained_memory_budget_bytes=2_000_000,
    )
    assert result["status"] == "PASS"
    assert result["memory_leak_sentinel"] == "PASS"
    assert result["retained_memory_growth_bytes"] <= result["retained_memory_budget_bytes"]
    assert result["exchange_orders_created"] == 1
    assert result["event_queue_final"] <= result["event_queue_max"]


def test_phase128_delivery_status_discloses_known_limitations_and_unresolved_risks():
    delivery = (ROOT / "docs/FINAL_DELIVERY_STATUS.md").read_text(encoding="utf-8")
    issues = (ROOT / "reports/KNOWN_ISSUES_LIMITATIONS.md").read_text(encoding="utf-8")
    combined = delivery + "\n" + issues
    for token in (
        "EXTERNAL_ACCEPTANCE_REQUIRED",
        "LIVE release remains fail-closed",
        "uv.lock",
        "frontend/package-lock.json",
        "TESTNET",
        "LIVE-shadow",
    ):
        assert token in combined


def test_phase129_coverage_runner_fallback_requires_each_file_and_real_coverage_data(monkeypatch, tmp_path):
    import subprocess as sp
    import scripts.local_coverage_runner as runner

    monkeypatch.setattr(runner, "ROOT", tmp_path)
    monkeypatch.setattr(runner, "REPORTS", tmp_path / "reports/local_coverage")
    monkeypatch.setattr(runner, "discover", lambda: ["tests/a.py", "tests/b.py"])
    monkeypatch.setattr(runner, "select_shard", lambda files, index, count: files)
    monkeypatch.setattr(runner, "_git_sha", lambda: "b" * 40)
    runner.REPORTS.mkdir(parents=True)
    calls = []

    class Proc:
        returncode = 0
        stdout = "1 passed\n"

    def fake_run(command, **kwargs):
        calls.append(command)
        if len(calls) == 1:
            raise sp.TimeoutExpired(command, kwargs.get("timeout", 1), output="2 passed\n")
        data = runner.REPORTS / ".coverage.00_of_01"
        data.write_bytes(data.read_bytes() + b"x" if data.exists() else b"x")
        return Proc()

    monkeypatch.setattr(runner, "run_captured", fake_run)
    payload = runner.run_shard(0, 1, 10)
    assert payload["status"] == "PASS"
    assert payload["execution_mode"] == "PER_FILE_TIMEOUT_FALLBACK"
    assert payload["blocker"] is None
    assert len(calls) == 3
    assert all("--append" in call for call in calls[1:])
