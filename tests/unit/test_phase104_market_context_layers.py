from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.data.point_in_time import ALLOWED_DATA_TYPES, AvailabilityRecord, PointInTimeStore
from app.research.derivatives import DerivativesSnapshot, build_derivatives_context
from app.research.event_risk import EconomicEvent, EventRiskPolicy, TRACKED_EVENT_TYPES
from app.research.onchain import OnChainSnapshot, build_onchain_context
from app.research.options_context import OptionsSnapshot, build_options_context
from app.research.reference_market import VenueQuote, build_reference_consensus

UTC = timezone.utc


def test_phase104_point_in_time_availability_tracks_all_required_semantics_and_macro_vintages():
    base = datetime(2026, 1, 1, 12, tzinfo=UTC)
    assert {
        "MACRO",
        "ETF_FLOW",
        "FUNDING",
        "OPEN_INTEREST",
        "LIQUIDATION",
        "ONCHAIN",
        "NEWS_SENTIMENT",
        "EXCHANGE_STATUS_FILTER",
    } <= ALLOWED_DATA_TYPES
    store = PointInTimeStore()
    original = AvailabilityRecord(
        "macro-1",
        "MACRO",
        "CPI",
        2.5,
        base,
        base + timedelta(minutes=1),
        base + timedelta(minutes=2),
        base + timedelta(minutes=3),
        "official-release",
        "vintage-1",
    )
    revision = AvailabilityRecord(
        "macro-2",
        "MACRO",
        "CPI",
        2.4,
        base,
        base + timedelta(days=30),
        base + timedelta(days=30, minutes=1),
        base + timedelta(days=30, minutes=2),
        "official-release",
        "vintage-2",
    )
    store.append(original)
    store.append(revision)
    assert store.latest_available(base + timedelta(hours=1), data_type="MACRO", key="CPI") == original
    assert store.latest_available(base + timedelta(days=31), data_type="MACRO", key="CPI") == revision
    for idx, kind in enumerate(sorted(ALLOWED_DATA_TYPES - {"MACRO"}), start=10):
        store.append(
            AvailabilityRecord(
                f"r-{idx}", kind, kind, 1.0, base, base, base, base + timedelta(seconds=1), "provider"
            )
        )
    assert {row.data_type for row in store.available_as_of(base + timedelta(hours=1))} >= ALLOWED_DATA_TYPES - {"MACRO"}


def test_phase104_reference_market_consensus_detects_divergence_spread_bad_tick_and_stale_feed():
    now = datetime(2026, 1, 1, 12, tzinfo=UTC)
    quotes = [
        VenueQuote("Binance", "BTCUSDT", 99.9, 100.1, 100.0, now, now, "binance-1"),
        VenueQuote("Coinbase", "BTCUSDT", 99.8, 100.2, 100.0, now, now, "coinbase-1"),
        VenueQuote("Kraken", "BTCUSDT", 99.9, 100.1, 100.0, now - timedelta(seconds=20), now - timedelta(seconds=20), "kraken-1"),
        VenueQuote("Bybit", "BTCUSDT", 99.9, 100.1, 103.0, now, now, "bybit-1"),
        VenueQuote("ApprovedVenue", "BTCUSDT", 99.0, 101.0, 100.0, now, now, "approved-1"),
    ]
    result = build_reference_consensus(quotes, as_of=now, max_age=timedelta(seconds=5), abnormal_spread_bps=100, bad_tick_deviation_bps=100)
    assert result.capability is True
    assert abs(result.reference_price - 100.0) < 1e-9
    assert "Kraken" in result.stale_venues
    assert "Bybit" in result.isolated_bad_tick_venues
    assert "ApprovedVenue" in result.abnormal_spread_venues
    assert result.exchange_specific_dislocation is True
    assert result.venue_divergence_bps is not None and result.venue_divergence_bps > 0
    assert {"Binance", "Coinbase"} <= set(result.contributing_venues)


def test_phase104_derivatives_context_is_point_in_time_deduplicated_non_triggering_and_gracefully_stale():
    now = datetime(2026, 1, 1, 12, tzinfo=UTC)
    common = dict(
        symbol="BTCUSDT",
        provider_id="provider-a",
        information_id="same-economic-observation",
        provider_timestamp=now,
        available_at=now,
        funding_rate=0.0001,
        predicted_funding_rate=0.0002,
        open_interest=1000.0,
        oi_change=0.1,
        futures_basis=0.02,
        annualized_basis=0.08,
        mark_index_basis=0.001,
        liquidation_intensity=0.3,
        liquidation_imbalance=-0.2,
        taker_buy_sell_imbalance=0.15,
        long_short_positioning=1.2,
        positioning_methodology_reliable=False,
    )
    first = DerivativesSnapshot(**common)
    duplicate = DerivativesSnapshot(**{**common, "provider_id": "provider-copy"})
    future = DerivativesSnapshot(**{**common, "information_id": "future-info", "available_at": now + timedelta(hours=1)})
    context = build_derivatives_context([first, duplicate, future], as_of=now)
    assert context.capability is True and context.standalone_trade_trigger_allowed is False
    assert context.contributing_information_ids == ("same-economic-observation",)
    required = {
        "funding_rate", "predicted_funding_rate", "open_interest", "oi_change", "futures_basis", "annualized_basis",
        "mark_index_basis", "liquidation_intensity", "liquidation_imbalance", "taker_buy_sell_imbalance", "long_short_positioning",
    }
    assert required <= set(context.features)
    assert context.features["long_short_positioning"] is None
    stale = build_derivatives_context([first], as_of=now + timedelta(hours=1), max_age=timedelta(minutes=5))
    assert stale.capability is False and stale.stale is True and stale.features == {}


def test_phase104_options_context_is_capability_gated_and_only_modifies_risk_context():
    now = datetime(2026, 1, 1, 12, tzinfo=UTC)
    missing = build_options_context(None, as_of=now)
    assert missing.capability is False and missing.features == {} and missing.position_size_multiplier == 1.0
    snapshot = OptionsSnapshot(
        symbol="BTCUSDT",
        event_time=now,
        available_at=now,
        atm_implied_volatility=0.70,
        term_structure=0.05,
        skew=-0.10,
        risk_reversal=-0.08,
        put_call_open_interest_or_volume=1.3,
        implied_expected_move=0.06,
        realized_volatility=0.50,
    )
    ctx = build_options_context(snapshot, as_of=now)
    assert ctx.capability is True and ctx.standalone_trade_trigger_allowed is False
    assert set(ctx.features) == {
        "atm_implied_volatility", "term_structure", "skew", "risk_reversal", "put_call_open_interest_or_volume",
        "implied_expected_move", "iv_realized_volatility_spread",
    }
    assert ctx.event_risk_score > 0 and ctx.volatility_expansion_score > 0 and ctx.tail_risk_score > 0
    assert ctx.stop_distance_multiplier > 1 and 0 < ctx.position_size_multiplier < 1


def test_phase104_onchain_context_uses_available_at_never_triggers_intraday_and_requires_oos_edge_for_weight():
    now = datetime(2026, 1, 1, 12, tzinfo=UTC)
    snapshot = OnChainSnapshot(
        asset="BTC",
        event_time=now - timedelta(hours=1),
        available_at=now,
        methodology_version="provider-method-v2",
        exchange_inflow=120,
        exchange_outflow=150,
        active_addresses=1_000_000,
        realized_cap_metric=500_000_000,
        mvrv=1.2,
        sopr=1.01,
        miner_related_flows=-5,
        stablecoin_exchange_flows=20,
        revised=True,
    )
    ctx = build_onchain_context(snapshot, as_of=now, requested_weight=0.2, oos_contribution_proven=False)
    assert ctx.capability is True
    assert ctx.features["net_exchange_flow"] == -30
    assert ctx.intraday_entry_trigger_allowed is False
    assert ctx.production_score_weight == 0.0
    assert ctx.provider_methodology_version == "provider-method-v2" and ctx.revision_or_latency_possible is True
    proven = build_onchain_context(snapshot, as_of=now, requested_weight=0.2, oos_contribution_proven=True)
    assert proven.production_score_weight == 0.2
    future = build_onchain_context(snapshot, as_of=now - timedelta(seconds=1), requested_weight=0.2, oos_contribution_proven=True)
    assert future.capability is False and future.production_score_weight == 0.0


def test_phase104_event_risk_engine_tracks_required_events_point_in_time_and_requires_oos_report_for_blackout():
    expected_types = {
        "FOMC", "FED_SPEECH", "NFP_EMPLOYMENT", "LIQUIDITY_RATE", "DXY_YIELDS_REAL_YIELDS",
        "SPOT_ETF_ETP_FLOW", "EXCHANGE_MAINTENANCE",
    }
    assert expected_types <= TRACKED_EVENT_TYPES
    scheduled = datetime(2026, 1, 1, 14, tzinfo=UTC)
    event = EconomicEvent(
        event_id="fomc-1",
        event_type="FOMC",
        scheduled_time=scheduled,
        actual_release_time=scheduled + timedelta(minutes=2),
        expected=4.0,
        actual=3.75,
        previous_vintage=4.25,
        surprise=-0.25,
        source="official-calendar",
        reliability=0.99,
    )
    before_release = event.as_of(scheduled)
    assert before_release.scheduled_time == scheduled
    assert before_release.actual_release_time is None and before_release.actual is None and before_release.surprise is None
    after_release = event.as_of(scheduled + timedelta(minutes=3))
    assert after_release.actual_release_time is not None and after_release.actual == 3.75 and after_release.previous_vintage == 4.25
    advisory = EventRiskPolicy(oos_effect_reported=False).evaluate(event, now=scheduled)
    assert advisory.production_policy_enabled is False and advisory.no_new_entry is False
    active = EventRiskPolicy(oos_effect_reported=True).evaluate(event, now=scheduled)
    assert active.production_policy_enabled is True and active.no_new_entry is True
    assert active.position_size_multiplier < 1 and active.slippage_assumption_multiplier > 1
    assert active.extra_confirmation_required is True
