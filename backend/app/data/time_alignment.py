from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
import time

@dataclass(frozen=True)
class AlignedCandle:
    timeframe:str
    open_time:datetime
    close_time:datetime
    payload:dict


def require_final(candle:AlignedCandle, decision_time:datetime)->AlignedCandle:
    if candle.open_time.tzinfo is None or candle.close_time.tzinfo is None or decision_time.tzinfo is None:
        raise ValueError('timezone-aware timestamps required')
    if candle.close_time <= candle.open_time:
        raise ValueError('close_time must be after open_time')
    if candle.close_time > decision_time:
        raise ValueError('future/non-final candle')
    return candle


def align_latest_final(candles:list[AlignedCandle], decision_time:datetime)->AlignedCandle:
    eligible=[require_final(c,decision_time) for c in candles if c.close_time<=decision_time]
    if not eligible: raise ValueError('no final candle available at decision time')
    return max(eligible,key=lambda c:c.close_time)


def align_multi_timeframe(series:dict[str,list[AlignedCandle]],decision_time:datetime)->dict[str,AlignedCandle]:
    return {tf:align_latest_final(rows,decision_time) for tf,rows in series.items()}

class MonotonicTimer:
    def __init__(self,clock=time.monotonic): self.clock=clock; self._last=None
    def sample(self)->float:
        value=float(self.clock())
        if self._last is not None and value < self._last: raise RuntimeError('MONOTONIC_CLOCK_REGRESSION')
        self._last=value; return value
    def elapsed(self,start:float)->float:
        end=self.sample()
        if end<start: raise RuntimeError('MONOTONIC_CLOCK_REGRESSION')
        return end-start
