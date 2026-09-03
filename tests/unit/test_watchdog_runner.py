from __future__ import annotations

import json

import httpx
import pytest

from scripts import watchdog_runner
from scripts.watchdog_runner import validate_http_url


@pytest.mark.parametrize(
    "url",
    ["http://app:8000/health", "https://alerts.example.test/hook"],
)
def test_validate_http_url_accepts_http_and_https(url: str) -> None:
    assert validate_http_url(url) == url


@pytest.mark.parametrize(
    "url",
    ["file:///etc/passwd", "ftp://example.test/file", "//example.test/path", "https:///missing-host"],
)
def test_validate_http_url_rejects_unsafe_or_incomplete_urls(url: str) -> None:
    with pytest.raises(ValueError, match=r"HTTP\(S\)"):
        validate_http_url(url)


def test_validate_http_url_rejects_embedded_credentials_and_bad_ports() -> None:
    with pytest.raises(ValueError, match="embedded credentials"):
        validate_http_url("https://user:secret@example.test/hook")
    with pytest.raises(ValueError):
        validate_http_url("https://example.test:99999/hook")


def test_fetch_json_uses_httpx_without_redirects(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: dict[str, object] = {}

    def fake_get(url: str, *, timeout: float, follow_redirects: bool) -> httpx.Response:
        seen.update(url=url, timeout=timeout, follow_redirects=follow_redirects)
        request = httpx.Request("GET", url)
        return httpx.Response(
            200,
            request=request,
            content=json.dumps({"ready_for_new_risk": True}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )

    monkeypatch.setattr(watchdog_runner.httpx, "get", fake_get)

    result = watchdog_runner.fetch_json("https://example.test/health", timeout=2.5)

    assert result == {"ready_for_new_risk": True}
    assert seen == {
        "url": "https://example.test/health",
        "timeout": 2.5,
        "follow_redirects": False,
    }


def test_fetch_json_rejects_non_object_json(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_get(url: str, *, timeout: float, follow_redirects: bool) -> httpx.Response:
        request = httpx.Request("GET", url)
        return httpx.Response(
            200,
            request=request,
            content=b"[]",
            headers={"Content-Type": "application/json"},
        )

    monkeypatch.setattr(watchdog_runner.httpx, "get", fake_get)

    with pytest.raises(ValueError, match="JSON object"):
        watchdog_runner.fetch_json("https://example.test/health")
