from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class SignalWeights:
    higher_tf_trend: float = 20
    ema_alignment: float = 15
    rsi_momentum: float = 12
    volume_confirmation: float = 10
    market_structure: float = 12
    pullback_completion: float = 10
    atr_normality: float = 8
    btc_volatility_penalty: float = 12


@dataclass(frozen=True)
class QualityDecision:
    score: float
    allowed: bool
    blockers: tuple[str, ...]
    contributors: tuple[str, ...]


def score_long_setup(features: dict, *, weights: SignalWeights | None = None, min_score: float = 55.0, min_rr: float = 2.0) -> QualityDecision:
    w = weights or SignalWeights()
    score = 0.0
    contributors=[]; blockers=[]

    def add(cond: bool, value: float, name: str):
        nonlocal score
        score += value if cond else -abs(value)*0.5
        contributors.append(f"{name}:{'PASS' if cond else 'FAIL'}")

    add(bool(features.get("higher_tf_bullish", False)), w.higher_tf_trend, "4H_BULLISH_TREND")
    add(float(features.get("ema21",0)) > float(features.get("ema50",0)), w.ema_alignment, "EMA21_GT_EMA50")
    add(float(features.get("rsi",0)) >= float(features.get("rsi_threshold",54)) and float(features.get("rsi_slope",0)) > 0, w.rsi_momentum, "RSI_54_RISING")
    add(float(features.get("volume_ratio",0)) >= 1.28, w.volume_confirmation, "VOLUME_PLUS_28")
    add(bool(features.get("bullish_structure",False)), w.market_structure, "BULLISH_STRUCTURE")
    add(bool(features.get("pullback_completed",False)), w.pullback_completion, "15M_PULLBACK_COMPLETE")
    add(not bool(features.get("atr_spike",False)), w.atr_normality, "ATR_NORMAL")
    if bool(features.get("btc_volatility_elevated",False)):
        score -= abs(w.btc_volatility_penalty); contributors.append("BTC_VOLATILITY_ELEVATED:PENALTY")

    checks=(
        (bool(features.get("lower_low_continuing",False)),"LOWER_LOW_CONTINUING"),
        (bool(features.get("negative_volume_expansion",False)),"NEGATIVE_VOLUME_EXPANSION"),
        (bool(features.get("breakdown",False)),"BREAKDOWN"),
        (bool(features.get("atr_spike",False)),"ATR_SPIKE"),
        (bool(features.get("liquidation_panic",False)),"LIQUIDATION_PANIC"),
        (bool(features.get("higher_tf_bearish",False)),"HIGHER_TF_BEARISH"),
        (float(features.get("stop_distance_fraction",0)) > float(features.get("max_stop_distance_fraction",0.06)),"STOP_TOO_WIDE"),
        (float(features.get("risk_reward",0)) < min_rr,"RISK_REWARD_INSUFFICIENT"),
    )
    blockers.extend(name for bad,name in checks if bad)
    score=max(0.0,min(100.0,score))
    return QualityDecision(score, score>=min_score and not blockers, tuple(blockers), tuple(contributors))
