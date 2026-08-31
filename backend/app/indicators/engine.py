from __future__ import annotations

import math

import numpy as np
import pandas as pd


def _finite(value: float, default: float = 0.0) -> float:
    value = float(value)
    return value if math.isfinite(value) else default


def indicators(rows: list[dict]) -> dict[str, float]:
    if not rows:
        raise ValueError("indicator input cannot be empty")
    df = pd.DataFrame(rows)
    close = pd.to_numeric(df["close"], errors="raise").astype(float)
    high = pd.to_numeric(df["high"], errors="raise").astype(float)
    low = pd.to_numeric(df["low"], errors="raise").astype(float)
    vol = pd.to_numeric(df["volume"], errors="raise").astype(float)
    if (close <= 0).any() or (high <= 0).any() or (low <= 0).any() or (vol < 0).any():
        raise ValueError("invalid OHLCV values")

    out: dict[str, float] = {}
    for n in (20, 50, 100, 200):
        out[f"sma{n}"] = _finite(close.rolling(n, min_periods=1).mean().iloc[-1])
    for n in (9, 21, 50, 200):
        out[f"ema{n}"] = _finite(close.ewm(span=n, adjust=False).mean().iloc[-1])

    typical = (high + low + close) / 3.0
    cumulative_volume = vol.cumsum().replace(0, np.nan)
    out["vwap"] = _finite(((typical * vol).cumsum() / cumulative_volume).iloc[-1], _finite(close.iloc[-1]))

    delta = close.diff()
    gain = delta.clip(lower=0).ewm(alpha=1 / 14, adjust=False, min_periods=1).mean()
    loss = (-delta.clip(upper=0)).ewm(alpha=1 / 14, adjust=False, min_periods=1).mean()
    rs = gain / loss.replace(0, np.nan)
    rsi = (100 - (100 / (1 + rs))).fillna(50).clip(0, 100)
    out["rsi"] = _finite(rsi.iloc[-1], 50.0)

    rsi_min = rsi.rolling(14, min_periods=1).min()
    rsi_max = rsi.rolling(14, min_periods=1).max()
    stoch_den = (rsi_max - rsi_min).replace(0, np.nan)
    stoch_rsi = (((rsi - rsi_min) / stoch_den) * 100).fillna(50).clip(0, 100)
    out["stoch_rsi"] = _finite(stoch_rsi.iloc[-1], 50.0)

    e12 = close.ewm(span=12, adjust=False).mean()
    e26 = close.ewm(span=26, adjust=False).mean()
    macd = e12 - e26
    macd_signal = macd.ewm(span=9, adjust=False).mean()
    out["macd"] = _finite(macd.iloc[-1])
    out["macd_signal"] = _finite(macd_signal.iloc[-1])
    roc = close.pct_change(10).replace([np.inf, -np.inf], np.nan).fillna(0)
    out["roc"] = _finite(roc.iloc[-1])

    prev_close = close.shift(1)
    tr = pd.concat([(high - low), (high - prev_close).abs(), (low - prev_close).abs()], axis=1).max(axis=1)
    atr = tr.ewm(alpha=1 / 14, adjust=False, min_periods=1).mean()
    out["atr"] = _finite(atr.iloc[-1])

    mid = close.rolling(20, min_periods=1).mean()
    sd = close.rolling(20, min_periods=1).std(ddof=0).fillna(0)
    out["bb_upper"] = _finite((mid + 2 * sd).iloc[-1])
    out["bb_lower"] = _finite((mid - 2 * sd).iloc[-1])
    out["bb_width"] = _finite(((4 * sd) / mid.replace(0, np.nan)).fillna(0).iloc[-1])
    log_returns = np.log(close / close.shift(1)).replace([np.inf, -np.inf], np.nan).fillna(0)
    out["historical_volatility"] = _finite(log_returns.rolling(20, min_periods=2).std(ddof=0).fillna(0).iloc[-1])

    volume_sma = vol.rolling(20, min_periods=1).mean()
    volume_ratio = vol / volume_sma.replace(0, np.nan)
    out["volume_sma"] = _finite(volume_sma.iloc[-1])
    out["volume_ratio"] = _finite(volume_ratio.fillna(0).iloc[-1])
    out["volume_spike"] = 1.0 if out["volume_ratio"] >= 1.5 else 0.0
    out["obv"] = _finite((np.sign(close.diff()).fillna(0) * vol).cumsum().iloc[-1])

    up_move = high.diff()
    down_move = -low.diff()
    plus_dm = pd.Series(np.where((up_move > down_move) & (up_move > 0), up_move, 0.0), index=df.index)
    minus_dm = pd.Series(np.where((down_move > up_move) & (down_move > 0), down_move, 0.0), index=df.index)
    wilder_atr = tr.ewm(alpha=1 / 14, adjust=False, min_periods=1).mean().replace(0, np.nan)
    plus_di = 100 * plus_dm.ewm(alpha=1 / 14, adjust=False, min_periods=1).mean() / wilder_atr
    minus_di = 100 * minus_dm.ewm(alpha=1 / 14, adjust=False, min_periods=1).mean() / wilder_atr
    dx = (100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)).fillna(0)
    adx = dx.ewm(alpha=1 / 14, adjust=False, min_periods=1).mean()
    out["di_plus"] = _finite(plus_di.fillna(0).iloc[-1])
    out["di_minus"] = _finite(minus_di.fillna(0).iloc[-1])
    out["adx"] = _finite(adx.iloc[-1])

    tail = min(20, len(close))
    x = np.arange(tail, dtype=float)
    out["trend_slope"] = _finite(np.polyfit(x, close.tail(tail), 1)[0]) if tail > 1 else 0.0

    window = min(20, len(df))
    recent_high = high.tail(window)
    recent_low = low.tail(window)
    out["support"] = _finite(recent_low.min())
    out["resistance"] = _finite(recent_high.max())
    if len(df) >= 4:
        split = max(2, min(10, len(df) // 2))
        prior_high = high.iloc[-2 * split : -split]
        current_high = high.iloc[-split:]
        prior_low = low.iloc[-2 * split : -split]
        current_low = low.iloc[-split:]
        out["higher_high"] = float(current_high.max() > prior_high.max())
        out["higher_low"] = float(current_low.min() > prior_low.min())
        out["lower_high"] = float(current_high.max() < prior_high.max())
        out["lower_low"] = float(current_low.min() < prior_low.min())
    else:
        out.update({"higher_high": 0.0, "higher_low": 0.0, "lower_high": 0.0, "lower_low": 0.0})

    if not all(math.isfinite(float(value)) for value in out.values()):
        raise ValueError("indicator output contains non-finite value")
    return out


def advanced_indicators(rows: list[dict], *, anchor_index: int = 0, volume_profile_bins: int = 24) -> dict[str, float]:
    """Point-in-time-safe advanced technical features from closed OHLCV bars only.

    Volume profile is an OHLCV approximation (typical-price buckets), not a trade-by-trade
    market-profile claim. Callers can distinguish this via ``volume_profile_quality``.
    """
    if not rows:
        raise ValueError("indicator input cannot be empty")
    if not 0 <= anchor_index < len(rows):
        raise ValueError("anchor_index out of range")
    if not 4 <= volume_profile_bins <= 200:
        raise ValueError("volume_profile_bins out of range")
    df = pd.DataFrame(rows)
    close = pd.to_numeric(df["close"], errors="raise").astype(float)
    high = pd.to_numeric(df["high"], errors="raise").astype(float)
    low = pd.to_numeric(df["low"], errors="raise").astype(float)
    open_ = pd.to_numeric(df.get("open", df["close"]), errors="raise").astype(float)
    vol = pd.to_numeric(df["volume"], errors="raise").astype(float)
    if (close <= 0).any() or (high <= 0).any() or (low <= 0).any() or (open_ <= 0).any() or (vol < 0).any():
        raise ValueError("invalid OHLCV values")

    out: dict[str, float] = {}
    window = min(20, len(df))
    donchian_high = high.rolling(window, min_periods=1).max()
    donchian_low = low.rolling(window, min_periods=1).min()
    out["donchian_upper"] = _finite(donchian_high.iloc[-1])
    out["donchian_lower"] = _finite(donchian_low.iloc[-1])
    out["donchian_mid"] = _finite(((donchian_high + donchian_low) / 2).iloc[-1])

    prev_close = close.shift(1)
    tr = pd.concat([(high-low), (high-prev_close).abs(), (low-prev_close).abs()], axis=1).max(axis=1)
    atr = tr.ewm(alpha=1/14, adjust=False, min_periods=1).mean()
    ema20 = close.ewm(span=20, adjust=False).mean()
    kc_upper = ema20 + 2 * atr
    kc_lower = ema20 - 2 * atr
    out["keltner_upper"] = _finite(kc_upper.iloc[-1])
    out["keltner_lower"] = _finite(kc_lower.iloc[-1])

    bb_mid = close.rolling(20, min_periods=1).mean()
    bb_sd = close.rolling(20, min_periods=1).std(ddof=0).fillna(0)
    bb_upper = bb_mid + 2 * bb_sd
    bb_lower = bb_mid - 2 * bb_sd
    out["bb_kc_squeeze"] = float(bb_upper.iloc[-1] <= kc_upper.iloc[-1] and bb_lower.iloc[-1] >= kc_lower.iloc[-1])

    typical = (high + low + close) / 3
    anchored_typical = typical.iloc[anchor_index:]
    anchored_vol = vol.iloc[anchor_index:]
    denom = float(anchored_vol.sum())
    out["anchored_vwap"] = _finite(float((anchored_typical * anchored_vol).sum()) / denom if denom > 0 else close.iloc[-1])

    # Session VWAP resets on an explicit session_id/date if supplied; otherwise the
    # provided batch is the session, which is deterministic and avoids timezone guesses.
    if "session_id" in df.columns:
        session = df["session_id"].iloc[-1]
        mask = df["session_id"] == session
        sess_typ, sess_vol = typical[mask], vol[mask]
    else:
        sess_typ, sess_vol = typical, vol
    sess_denom = float(sess_vol.sum())
    out["session_vwap"] = _finite(float((sess_typ * sess_vol).sum()) / sess_denom if sess_denom > 0 else close.iloc[-1])

    mean20 = close.rolling(20, min_periods=2).mean()
    sd20 = close.rolling(20, min_periods=2).std(ddof=0)
    z = ((close - mean20) / sd20.replace(0, np.nan)).fillna(0)
    out["rolling_zscore"] = _finite(z.iloc[-1])

    log_hl = np.log(high / low)
    parkinson_var = (log_hl.pow(2).rolling(20, min_periods=2).mean() / (4 * math.log(2))).fillna(0)
    out["parkinson_volatility"] = _finite(math.sqrt(max(0.0, float(parkinson_var.iloc[-1]))))
    log_co = np.log(close / open_)
    gk_var = (0.5 * log_hl.pow(2) - (2 * math.log(2) - 1) * log_co.pow(2)).rolling(20, min_periods=2).mean().fillna(0)
    out["garman_klass_volatility"] = _finite(math.sqrt(max(0.0, float(gk_var.iloc[-1]))))

    # Confirmed swing points exclude the current bar to avoid repainting a still-open pivot.
    radius = 2
    swing_highs: list[float] = []
    swing_lows: list[float] = []
    for i in range(radius, max(radius, len(df)-radius)):
        hs = high.iloc[i-radius:i+radius+1]
        ls = low.iloc[i-radius:i+radius+1]
        if high.iloc[i] == hs.max() and int((hs == high.iloc[i]).sum()) == 1:
            swing_highs.append(float(high.iloc[i]))
        if low.iloc[i] == ls.min() and int((ls == low.iloc[i]).sum()) == 1:
            swing_lows.append(float(low.iloc[i]))
    out["swing_high"] = _finite(swing_highs[-1] if swing_highs else high.iloc[:-1].max() if len(high)>1 else high.iloc[-1])
    out["swing_low"] = _finite(swing_lows[-1] if swing_lows else low.iloc[:-1].min() if len(low)>1 else low.iloc[-1])

    # Kaufman efficiency ratio and choppiness index, both bounded/finite.
    n = min(14, max(1, len(close)-1))
    direction = abs(float(close.iloc[-1] - close.iloc[-1-n])) if len(close) > n else 0.0
    path = float(close.diff().abs().tail(n).sum())
    out["trend_efficiency"] = _finite(direction / path if path > 0 else 0.0)
    hh = float(high.tail(n).max()); ll = float(low.tail(n).min()); trsum = float(tr.tail(n).sum())
    if n > 1 and hh > ll and trsum > 0:
        chop = 100 * math.log10(trsum / (hh-ll)) / math.log10(n)
    else:
        chop = 0.0
    out["choppiness"] = _finite(min(100.0, max(0.0, chop)))

    # OHLCV-approximate volume profile. Require enough variation and non-zero volume;
    # otherwise explicitly expose quality=0 and use last price rather than fabricate POC.
    lo, hi = float(low.min()), float(high.max())
    total_vol = float(vol.sum())
    if len(df) >= 10 and hi > lo and total_vol > 0:
        edges = np.linspace(lo, hi, volume_profile_bins + 1)
        bucket = np.clip(np.digitize(typical.to_numpy(), edges) - 1, 0, volume_profile_bins - 1)
        bucket_vol = np.bincount(bucket, weights=vol.to_numpy(), minlength=volume_profile_bins)
        poc_idx = int(np.argmax(bucket_vol)); centers = (edges[:-1] + edges[1:]) / 2
        order = np.argsort(bucket_vol)[::-1]; running = 0.0; selected=[]
        for idx in order:
            selected.append(int(idx)); running += float(bucket_vol[idx])
            if running >= total_vol * 0.70: break
        out["volume_poc"] = _finite(centers[poc_idx])
        out["value_area_low"] = _finite(min(centers[selected]))
        out["value_area_high"] = _finite(max(centers[selected]))
        out["volume_profile_quality"] = 1.0
    else:
        out["volume_poc"] = _finite(close.iloc[-1])
        out["value_area_low"] = _finite(close.iloc[-1])
        out["value_area_high"] = _finite(close.iloc[-1])
        out["volume_profile_quality"] = 0.0

    if not all(math.isfinite(float(value)) for value in out.values()):
        raise ValueError("advanced indicator output contains non-finite value")
    return out
