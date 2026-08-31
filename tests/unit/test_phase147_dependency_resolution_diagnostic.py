from scripts import dependency_resolution_diagnostic as d


def test_phase147_offline_registry_classification(monkeypatch, tmp_path):
    monkeypatch.setattr(d, "ROOT", tmp_path)
    (tmp_path / "frontend").mkdir()
    (tmp_path / "pyproject.toml").write_text("[project]\nname='x'\n", encoding="utf-8")
    (tmp_path / "frontend/package.json").write_text("{}\n", encoding="utf-8")
    monkeypatch.setattr(d.shutil, "which", lambda name: f"/bin/{name}")

    def fail_dns(*args, **kwargs):
        raise OSError("offline")

    monkeypatch.setattr(d.socket, "getaddrinfo", fail_dns)
    payload = d.evaluate()
    assert payload["summary"]["manifests_ready"] is True
    assert payload["summary"]["tools_ready"] is True
    assert payload["summary"]["registries_resolvable"] is False
    assert "REGISTRY_DNS_UNAVAILABLE" in payload["summary"]["blockers"]
    assert "SOURCE_LOCKS_MISSING" in payload["summary"]["blockers"]
    assert payload["summary"]["next_action"] == "RUN_LOCK_PROMOTION_IN_NETWORKED_TRUSTED_CI"


def test_phase147_existing_locks_prioritize_verification(monkeypatch, tmp_path):
    monkeypatch.setattr(d, "ROOT", tmp_path)
    (tmp_path / "frontend").mkdir()
    for rel, body in (
        ("pyproject.toml", "[project]\nname='x'\n"),
        ("frontend/package.json", "{}\n"),
        ("uv.lock", "version = 1\n"),
        ("frontend/package-lock.json", '{"lockfileVersion":3}\n'),
    ):
        (tmp_path / rel).write_text(body, encoding="utf-8")
    monkeypatch.setattr(d.shutil, "which", lambda name: f"/bin/{name}")
    monkeypatch.setattr(d.socket, "getaddrinfo", lambda *a, **k: [(None, None, None, None, ("127.0.0.1", 443))])
    payload = d.evaluate()
    assert payload["summary"]["locks_present"] is True
    assert payload["summary"]["next_action"] == "VERIFY_COMMITTED_SOURCE_LOCKS"
