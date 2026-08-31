from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
import uuid
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from sqlalchemy import select
from app.database.models import SetupState

SECRET_KEYS = {"api_key", "api_secret", "secret", "token", "password", "telegram_bot_token", "binance_api_key", "binance_api_secret"}
STEPS = tuple(range(1, 9))


def _clean(value):
    if isinstance(value, dict):
        return {k: _clean(v) for k, v in value.items() if k.casefold() not in SECRET_KEYS and not any(x in k.casefold() for x in ("secret", "password", "token", "api_key"))}
    if isinstance(value, list):
        return [_clean(v) for v in value]
    return value


def _validate_preferences(data: dict) -> dict:
    out = dict(data)
    timezone_name = str(out.get("timezone", "UTC")).strip()
    try:
        ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError as exc:
        raise ValueError("invalid IANA timezone") from exc
    out["timezone"] = timezone_name
    notifications = out.get("notifications", {})
    if not isinstance(notifications, dict):
        raise ValueError("notifications must be an object")
    allowed = {"telegram", "email", "critical_only"}
    unknown = set(notifications) - allowed
    if unknown:
        raise ValueError("unknown notification preferences: " + ",".join(sorted(unknown)))
    if any(not isinstance(v, bool) for v in notifications.values()):
        raise ValueError("notification preferences must be boolean")
    out["notifications"] = {k: bool(notifications.get(k, False)) for k in sorted(allowed)}
    return out


@dataclass(frozen=True)
class WizardSnapshot:
    setup_id: str
    current_step: int
    completed_steps: tuple[int, ...]
    non_secret_config: dict
    completed: bool
    startup_mode: str


class SetupWizardService:
    def __init__(self, session_factory):
        self.sf = session_factory

    def start_or_resume(self, user_id: str | None = None, setup_id: str = "default") -> WizardSnapshot:
        with self.sf() as session:
            row = session.get(SetupState, setup_id)
            if row is None:
                row = SetupState(id=setup_id, user_id=user_id, current_step=1, completed_steps=[], non_secret_config={})
                session.add(row)
                session.commit()
            return self._snapshot(row)

    def complete_step(self, setup_id: str, step: int, data: dict) -> WizardSnapshot:
        if step not in STEPS:
            raise ValueError("wizard step out of range")
        with self.sf() as session:
            row = session.get(SetupState, setup_id)
            if row is None:
                raise LookupError("setup state not found")
            completed = list(row.completed_steps or [])
            expected = min(set(STEPS) - set(completed), default=8)
            if step != expected and step not in completed:
                raise ValueError("wizard steps must complete sequentially")
            config = dict(row.non_secret_config or {})
            cleaned = _clean(data)
            if step == 7:
                cleaned = _validate_preferences(cleaned)
            config[f"step_{step}"] = cleaned
            if step not in completed:
                completed.append(step)
            row.completed_steps = sorted(completed)
            row.non_secret_config = config
            row.current_step = min(8, step + 1)
            if set(row.completed_steps) == set(STEPS):
                final = config.get("step_8", {})
                if not final.get("preflight_ok", False):
                    raise PermissionError("final preflight must pass")
                row.completed_at = datetime.now(timezone.utc)
                row.current_step = 8
            session.commit()
            session.refresh(row)
            return self._snapshot(row)

    @staticmethod
    def _snapshot(row: SetupState) -> WizardSnapshot:
        # First startup is always PAPER, regardless of a requested future LIVE mode.
        return WizardSnapshot(row.id, row.current_step, tuple(row.completed_steps or []), dict(row.non_secret_config or {}), row.completed_at is not None, "PAPER")

RISK_PRESETS = {
    "MUHAFAZAKAR": {"risk_per_trade": "0.0015", "max_open_positions": 3},
    "DENGELI": {"risk_per_trade": "0.0025", "max_open_positions": 6},
    "AGRESIF": {"risk_per_trade": "0.0050", "max_open_positions": 8},
}


def validate_setup_profile(profile: dict) -> dict:
    """Validate first-run non-secret configuration without requiring terminal edits.

    Connection probes are supplied as facts by the API/UI layer. This function does
    not fabricate exchange, Redis, database or TESTNET acceptance; it only enforces
    the safety contract before a persisted setup can be considered locally valid.
    """
    out = _clean(dict(profile))
    health = out.get("health") or {}
    for key in ("server", "database", "redis", "clock_sync"):
        if health.get(key) is not True:
            raise ValueError(f"setup health check failed: {key}")
    version = str(out.get("version", "")).strip()
    if not version:
        raise ValueError("version is required")
    exchange = out.get("exchange") or {}
    if not exchange.get("name"):
        raise ValueError("exchange selection is required")
    if exchange.get("connection_ok") is not True or exchange.get("permission_test_ok") is not True:
        raise ValueError("exchange connection/permission test must pass")
    if exchange.get("withdrawal_enabled") is True:
        raise PermissionError("withdrawal permission must be disabled")
    if not exchange.get("account_mode") or not exchange.get("market_capabilities"):
        raise ValueError("account mode and market capability discovery are required")

    notifications = out.get("notifications") or {}
    if notifications.get("enabled"):
        if not notifications.get("channel_id") or notifications.get("test_message_ok") is not True:
            raise ValueError("notification channel and test message are required")
        if notifications.get("state_changing_commands_enabled") is True:
            raise PermissionError("state-changing notification commands default to disabled")

    requested_mode = str(out.get("requested_mode", "PAPER")).upper()
    if requested_mode not in {"PAPER", "TESTNET", "LIVE"}:
        raise ValueError("unsupported requested mode")
    if requested_mode == "LIVE" and out.get("live_gate_pass") is not True:
        raise PermissionError("LIVE remains locked until release gate passes")

    preset = str(out.get("risk_preset", "DENGELI")).upper()
    if preset not in {*RISK_PRESETS, "OZEL", "OTOMATIK_UYGUNLUK"}:
        raise ValueError("unsupported risk preset")
    out["risk_preset"] = preset
    out["risk_preset_is_magic"] = False
    if preset == "OTOMATIK_UYGUNLUK":
        out["risk_preset_behavior"] = "RECOMMEND_ONLY"

    universe = out.get("universe") or {}
    if not isinstance(universe.get("allowlist", []), list) or not isinstance(universe.get("blocklist", []), list):
        raise ValueError("allowlist/blocklist must be lists")
    if not universe.get("quote_asset"):
        raise ValueError("quote asset is required")
    max_size = int(universe.get("max_universe_size", 0))
    if max_size < 1 or max_size > 1000:
        raise ValueError("max universe size out of range")
    if universe.get("new_listing_policy") not in {"QUARANTINE", "BLOCK", "ALLOW_AFTER_MIN_AGE"}:
        raise ValueError("new listing policy is required")

    prefs = _validate_preferences({
        "timezone": out.get("timezone", "UTC"),
        "notifications": {"telegram": False, "email": False, "critical_only": True},
    })
    out["timezone"] = prefs["timezone"]
    if out.get("number_format") not in {"tr-TR", "en-US"}:
        raise ValueError("number/date format must be explicit")
    if out.get("language") not in {"tr", "en"}:
        raise ValueError("language must be explicit")
    checklist = out.get("security_checklist") or {}
    if not checklist or not all(v is True for v in checklist.values()):
        raise PermissionError("security checklist incomplete")
    out["startup_mode"] = "PAPER"
    return out
