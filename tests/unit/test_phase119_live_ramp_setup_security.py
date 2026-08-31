from __future__ import annotations

from decimal import Decimal
from pathlib import Path
import pytest

from app.risk.live_ramp import LiveRamp, LiveRampEvidence, LiveRampPolicy, STAGES
from app.services.setup_wizard import validate_setup_profile

ROOT = Path(__file__).resolve().parents[2]


def good_evidence(**overrides):
    data = dict(
        reconciliation_pass=True,
        unresolved_critical_incidents=0,
        protective_order_success_rate=Decimal("0.999"),
        live_slippage_bps=Decimal("10"),
        live_shadow_divergence_bps=Decimal("12"),
        net_expectancy=Decimal("0.002"),
        expectancy_lower_confidence_bound=Decimal("0.0001"),
        drawdown=Decimal("0.03"),
        effective_sample_size=Decimal("80"),
        market_conditions_observed=3,
        strategy_degraded=False,
    )
    data.update(overrides)
    return LiveRampEvidence(**data)


def test_phase119_live_ramp_evidence_gate_is_numeric_bounded_explainable_and_human_only_upward():
    ramp = LiveRamp()
    assert tuple(ramp.policy.stage_multipliers) == STAGES
    assert ramp.risk_multiplier == Decimal("0.10")
    with pytest.raises(PermissionError, match="automatic live risk increase disabled"):
        ramp.increase(good_evidence())
    assert ramp.increase(good_evidence(), human_approved=True) == "LIVE_STAGE_1"
    assert ramp.risk_multiplier == Decimal("0.25")
    assert ramp.decrease() == "LIVE_STAGE_0"


def test_phase119_live_ramp_blocks_every_required_operational_and_profitability_condition():
    p = LiveRampPolicy()
    cases = {
        "RECONCILIATION_NOT_PASS": dict(reconciliation_pass=False),
        "CRITICAL_INCIDENTS_UNRESOLVED": dict(unresolved_critical_incidents=1),
        "PROTECTIVE_ORDER_SUCCESS_TOO_LOW": dict(protective_order_success_rate=Decimal("0.90")),
        "LIVE_SLIPPAGE_TOO_HIGH": dict(live_slippage_bps=Decimal("99")),
        "LIVE_SHADOW_DIVERGENCE_TOO_HIGH": dict(live_shadow_divergence_bps=Decimal("99")),
        "NET_EXPECTANCY_UNACCEPTABLE": dict(expectancy_lower_confidence_bound=Decimal("-0.001")),
        "DRAWDOWN_TOO_HIGH": dict(drawdown=Decimal("0.20")),
        "EFFECTIVE_SAMPLE_TOO_SMALL": dict(effective_sample_size=Decimal("5")),
        "INSUFFICIENT_MARKET_CONDITIONS": dict(market_conditions_observed=1),
        "STRATEGY_DEGRADED": dict(strategy_degraded=True),
    }
    for expected, override in cases.items():
        assert expected in p.blockers(good_evidence(**override))
    assert p.eligible(good_evidence())


def valid_profile():
    return {
        "health": {"server": True, "database": True, "redis": True, "clock_sync": True},
        "version": "0.3.0-local-acceptance",
        "exchange": {
            "name": "BINANCE", "connection_ok": True, "permission_test_ok": True,
            "withdrawal_enabled": False, "account_mode": "SPOT",
            "market_capabilities": ["SPOT"],
        },
        "notifications": {"enabled": True, "channel_id": "chat-redacted", "test_message_ok": True, "state_changing_commands_enabled": False},
        "requested_mode": "TESTNET",
        "live_gate_pass": False,
        "risk_preset": "OTOMATIK_UYGUNLUK",
        "universe": {"allowlist": [], "blocklist": [], "quote_asset": "USDT", "max_universe_size": 50, "new_listing_policy": "QUARANTINE"},
        "timezone": "Europe/Istanbul", "number_format": "tr-TR", "language": "tr",
        "security_checklist": {"mfa": True, "withdrawal_disabled": True, "backup_key": True},
        "api_secret": "never-persist-this",
    }


def test_phase119_first_run_profile_covers_health_exchange_notification_risk_universe_locale_security_and_forces_paper():
    out = validate_setup_profile(valid_profile())
    assert out["startup_mode"] == "PAPER"
    assert out["risk_preset_behavior"] == "RECOMMEND_ONLY"
    assert out["risk_preset_is_magic"] is False
    assert "api_secret" not in out
    assert out["timezone"] == "Europe/Istanbul"


def test_phase119_first_run_profile_rejects_withdrawal_permission_live_without_gate_and_unsafe_commands():
    p = valid_profile(); p["exchange"]["withdrawal_enabled"] = True
    with pytest.raises(PermissionError, match="withdrawal"):
        validate_setup_profile(p)
    p = valid_profile(); p["requested_mode"] = "LIVE"
    with pytest.raises(PermissionError, match="LIVE"):
        validate_setup_profile(p)
    p = valid_profile(); p["notifications"]["state_changing_commands_enabled"] = True
    with pytest.raises(PermissionError, match="state-changing"):
        validate_setup_profile(p)


def test_phase119_tls_trusted_proxy_and_encrypted_backup_delivery_contracts_are_fail_closed():
    nginx = (ROOT / "docker/nginx/nginx.prod.conf").read_text(encoding="utf-8")
    backup = (ROOT / "scripts/backup.sh").read_text(encoding="utf-8")
    hardening = (ROOT / "docs/SECURITY_HARDENING.md").read_text(encoding="utf-8")
    assert "listen 8443 ssl" in nginx and "TLSv1.2 TLSv1.3" in nginx
    assert "X-Forwarded-Proto https" in nginx and "X-Forwarded-For" in nginx
    assert "umask 077" in backup and "backup_crypto.py encrypt" in backup and "chmod 600" in backup
    assert "reverse-proxy/firewall boundary" in hardening
