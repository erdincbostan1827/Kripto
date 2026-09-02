from __future__ import annotations

import pytest

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
