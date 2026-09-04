from __future__ import annotations

import os
import re
from collections.abc import Mapping

_SENSITIVE_NAME = re.compile(r"(?:KEY|SECRET|TOKEN|PASSWORD|PASSWD|CREDENTIAL|PRIVATE|AUTH|SIGNATURE)", re.I)
_BEARER = re.compile(r"(?i)\b(Bearer\s+)[A-Za-z0-9._~+/=-]{8,}")
_BASIC = re.compile(r"(?i)\b(Basic\s+)[A-Za-z0-9+/=]{8,}")
_URL_USERINFO = re.compile(r"(https?://)([^\s/@:]+):([^\s/@]+)@", re.I)
_QUERY_SECRET = re.compile(r"(?i)([?&](?:api[_-]?key|token|access[_-]?token|secret|signature|password)=)[^&\s]+")
_ASSIGN_SECRET = re.compile(r"(?i)\b(api[_-]?key|token|access[_-]?token|secret|signature|password)\s*[:=]\s*([^\s,;]+)")


def sensitive_values(env: Mapping[str, str] | None = None) -> list[str]:
    env = os.environ if env is None else env
    values: list[str] = []
    for name, value in env.items():
        if value and len(value) >= 6 and _SENSITIVE_NAME.search(name):
            values.append(value)
    return sorted(set(values), key=len, reverse=True)


def redact_text(text: str, env: Mapping[str, str] | None = None) -> str:
    """Best-effort redaction for logs/evidence. Never returns known sensitive env values."""
    safe = text or ""
    for value in sensitive_values(env):
        safe = safe.replace(value, "[REDACTED]")
    safe = _BEARER.sub(r"\1[REDACTED]", safe)
    safe = _BASIC.sub(r"\1[REDACTED]", safe)
    safe = _URL_USERINFO.sub(r"\1[REDACTED]@", safe)
    safe = _QUERY_SECRET.sub(r"\1[REDACTED]", safe)
    safe = _ASSIGN_SECRET.sub(lambda m: f"{m.group(1)}=[REDACTED]", safe)
    return safe


def classify_blocker(output: str, returncode: int | None, *, tool: str | None = None) -> str:
    """Return a stable, non-secret blocker category from command output."""
    text = (output or "").lower()
    if "modulenotfounderror" in text or "no module named" in text:
        return "RUNTIME_DEPENDENCY_MISSING"
    if any(p in text for p in (
        "could not resolve", "temporary failure in name resolution", "name or service not known",
        "getaddrinfo", "enotfound", "dns lookup failed",
    )):
        return "NETWORK_DNS_UNAVAILABLE"
    if any(p in text for p in (
        "not found in cache", "not found in the cache", "offline mode", "offline cache", "no matching package named",
        "cache miss", "cached metadata", "enotcached", "no cached response", "network was disabled",
    )):
        return "OFFLINE_CACHE_INCOMPLETE"
    if any(p in text for p in ("unauthorized", "authentication failed", "invalid credential", "http 401", "status code 401")):
        return "AUTHENTICATION_FAILED"
    if any(p in text for p in ("forbidden", "http 403", "status code 403", "not authorized")):
        return "AUTHORIZATION_FAILED"
    if "permission denied" in text or "operation not permitted" in text:
        return "PERMISSION_DENIED"
    if any(p in text for p in ("connection refused", "failed to connect", "network is unreachable", "no route to host")):
        return "NETWORK_ENDPOINT_UNAVAILABLE"
    if any(p in text for p in ("timed out", "timeout", "etimedout")):
        return "COMMAND_OR_NETWORK_TIMEOUT"
    if any(p in text for p in ("cannot connect to the docker daemon", "docker daemon is not running", "is the docker daemon running")):
        return "CONTAINER_RUNTIME_UNAVAILABLE"
    if any(p in text for p in ("no such file or directory", "file not found", "cannot find the file")):
        return "REQUIRED_FILE_MISSING"
    if returncode is None:
        return f"TOOL_UNAVAILABLE:{tool}" if tool else "TOOL_OR_PROCESS_UNAVAILABLE"
    return f"EXIT_CODE:{returncode}"
