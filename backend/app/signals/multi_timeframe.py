from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from app.core.enums import Signal
from app.services.pipeline import analyze


@dataclass(frozen=True)
class MultiTimeframeDecision:
    signal: Signal
    score: int
    conflict: bool
    higher_timeframe_bias: str
    timeframe_scores: dict[str, int]
    reasons: tuple[str, ...]


DEFAULT_WEIGHTS = {"1d": 0.25, "4h": 0.25, "1h": 0.20, "15m": 0.20, "5m": 0.10}


def analyze_multi_timeframe(candles_by_timeframe: Mapping[str, list[dict]], weights: Mapping[str, float] | None = None) -> MultiTimeframeDecision:
    weights = dict(weights or DEFAULT_WEIGHTS)
    missing = [tf for tf in weights if tf not in candles_by_timeframe]
    if missing:
        raise ValueError(f"missing required timeframes: {','.join(missing)}")
    if abs(sum(weights.values()) - 1.0) > 1e-9 or any(value <= 0 for value in weights.values()):
        raise ValueError("multi-timeframe weights must be positive and sum to 1")

    decisions = {tf: analyze(candles_by_timeframe[tf], tf) for tf in weights}
    score = int(round(sum(decisions[tf].score * weight for tf, weight in weights.items())))
    higher = [decisions[tf].regime for tf in ("1d", "4h", "1h") if tf in decisions]
    bearish = sum(value == "BEARISH_TREND" for value in higher)
    bullish = sum(value == "BULLISH_TREND" for value in higher)
    bias = "BEARISH" if bearish >= 2 else "BULLISH" if bullish >= 2 else "MIXED"
    low_tf_bullish = any(decisions[tf].signal in {Signal.BUY, Signal.STRONG_BUY} for tf in ("15m", "5m") if tf in decisions)
    conflict = bias == "BEARISH" and low_tf_bullish

    if conflict:
        signal = Signal.NO_TRADE
    elif bias == "BULLISH" and score >= 75:
        signal = Signal.BUY if score < 85 else Signal.STRONG_BUY
    elif bias == "BEARISH":
        signal = Signal.NO_TRADE
    elif score >= 60:
        signal = Signal.WATCH
    else:
        signal = Signal.HOLD
    reasons = tuple(f"{tf}:{decisions[tf].regime}:{decisions[tf].score}" for tf in weights)
    if conflict:
        reasons += ("MULTI_TIMEFRAME_CONFLICT",)
    return MultiTimeframeDecision(signal, score, conflict, bias, {tf: decisions[tf].score for tf in weights}, reasons)
