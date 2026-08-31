import pytest
from app.signals.decision_quality import SignalWeights, score_long_setup
from app.strategies.regime_extended import detect_extended_regime
from app.strategies.outcomes import SignalOutcome, summarize_outcomes
from app.signals.multi_timeframe import DEFAULT_WEIGHTS


def _good():
    return {"higher_tf_bullish":True,"ema21":110,"ema50":100,"rsi":58,"rsi_threshold":54,"rsi_slope":2,"volume_ratio":1.4,"bullish_structure":True,"pullback_completed":True,"atr_spike":False,"btc_volatility_elevated":False,"stop_distance_fraction":.03,"max_stop_distance_fraction":.06,"risk_reward":2.5}


def test_phase110_configurable_signal_weights_score_4h_1h_rsi_volume_structure_pullback_atr_and_btc_volatility():
    base=score_long_setup(_good())
    assert base.allowed and base.score>=55
    custom=score_long_setup(_good(),weights=SignalWeights(volume_confirmation=30))
    assert custom.score>=base.score
    stressed=dict(_good(),btc_volatility_elevated=True)
    assert score_long_setup(stressed).score < base.score


def test_phase110_falling_knife_gate_blocks_every_required_deterioration_condition():
    keys=["lower_low_continuing","negative_volume_expansion","breakdown","atr_spike","liquidation_panic","higher_tf_bearish"]
    for key in keys:
        row=dict(_good()); row[key]=True
        out=score_long_setup(row)
        assert not out.allowed and out.blockers
    row=dict(_good(),stop_distance_fraction=.2)
    assert "STOP_TOO_WIDE" in score_long_setup(row).blockers
    row=dict(_good(),risk_reward=1.2)
    assert "RISK_REWARD_INSUFFICIENT" in score_long_setup(row).blockers


def test_phase110_extended_regime_detects_low_vol_panic_breakout_breakdown_and_uses_vol_ma_structure_volume():
    common={"price":100,"support":90,"resistance":110,"ema21":105,"ema50":100,"trend_slope":1,"higher_high":1,"lower_low":0,"volume_ratio":1,"historical_volatility":.02,"bb_width":.04}
    assert detect_extended_regime(dict(common,historical_volatility=.001,bb_width=.01)).regime=="LOW_VOLATILITY"
    assert detect_extended_regime(dict(common,liquidation_panic=True)).regime=="PANIC"
    assert detect_extended_regime(dict(common,price=112,volume_ratio=1.4)).regime=="BREAKOUT"
    assert detect_extended_regime(dict(common,price=88,volume_ratio=1.4)).regime=="BREAKDOWN"
    assert detect_extended_regime(common).regime=="BULLISH_TREND"


def test_phase110_multi_timeframe_analysis_has_configurable_normalized_weights_contract():
    assert set(DEFAULT_WEIGHTS)=={"1d","4h","1h","15m","5m"}
    assert sum(DEFAULT_WEIGHTS.values())==pytest.approx(1)


def test_phase110_model_health_outcomes_store_outcome_return_and_time_to_tp_sl_and_detect_degradation():
    good=SignalOutcome("x","TP",.02,time_to_tp_seconds=300)
    bad=[SignalOutcome(str(i),"SL",-.01,time_to_sl_seconds=120) for i in range(25)]
    assert summarize_outcomes([good])["win_rate"]==1
    s=summarize_outcomes(bad)
    assert s["degraded"] and s["mean_return"]<0 and s["samples"]==25
