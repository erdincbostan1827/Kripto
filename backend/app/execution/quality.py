from __future__ import annotations
from dataclasses import dataclass
from decimal import Decimal
from statistics import mean

D=Decimal

@dataclass(frozen=True)
class ExecutionObservation:
    side:str
    reference_price:D
    quoted_bid:D
    quoted_ask:D
    expected_price:D
    fill_price:D | None
    quantity:D
    requested_quantity:D
    ack_ms:float
    fill_ms:float | None
    cancelled:bool=False
    rejected:bool=False
    maker:bool=False
    post_fill_mark:D | None=None

@dataclass(frozen=True)
class ExecutionQuality:
    quoted_spread_bps:float
    effective_spread_bps:float
    realized_slippage_bps:float
    expected_slippage_bps:float
    fill_ratio:float
    partial_fill_ratio:float
    cancel_ratio:float
    reject_ratio:float
    avg_ack_ms:float
    avg_fill_ms:float
    market_impact_bps:float
    adverse_selection_bps:float
    maker_ratio:float


def _signed_cost_bps(side, px, ref):
    sign=D('1') if side.upper()=='BUY' else D('-1')
    return float(sign*(D(px)-D(ref))/D(ref)*D('10000'))


def summarize_execution_quality(rows:list[ExecutionObservation])->ExecutionQuality:
    if not rows: raise ValueError('execution observations required')
    spreads=[]; eff=[]; slip=[]; expected=[]; fills=[]; partial=[]; impact=[]; adverse=[]; fill_times=[]
    for r in rows:
        ref=D(r.reference_price)
        if ref<=0 or D(r.requested_quantity)<=0: raise ValueError('invalid execution observation')
        spreads.append(float((D(r.quoted_ask)-D(r.quoted_bid))/ref*D('10000')))
        ratio=float(max(D('0'),min(D('1'),D(r.quantity)/D(r.requested_quantity))))
        fills.append(ratio); partial.append(1.0 if D('0')<D(r.quantity)<D(r.requested_quantity) else 0.0)
        expected.append(_signed_cost_bps(r.side,r.expected_price,ref))
        if r.fill_price is not None:
            eff.append(_signed_cost_bps(r.side,r.fill_price,ref)*2)
            impact.append(_signed_cost_bps(r.side,r.fill_price,ref))
            slip.append(_signed_cost_bps(r.side,r.fill_price,r.expected_price))
            if r.post_fill_mark is not None: adverse.append(_signed_cost_bps(r.side,r.post_fill_mark,r.fill_price)*-1)
        if r.fill_ms is not None: fill_times.append(float(r.fill_ms))
    return ExecutionQuality(
        mean(spreads), mean(eff) if eff else 0.0, mean(slip) if slip else 0.0,
        mean(expected), mean(fills), mean(partial),
        sum(1 for r in rows if r.cancelled)/len(rows), sum(1 for r in rows if r.rejected)/len(rows),
        mean(float(r.ack_ms) for r in rows), mean(fill_times) if fill_times else 0.0,
        mean(impact) if impact else 0.0, mean(adverse) if adverse else 0.0, sum(1 for r in rows if r.maker)/len(rows)
    )


def execution_quality_score(q: ExecutionQuality, *, available_liquidity_ratio: float = 1.0) -> float:
    """Return a bounded 0..100 execution-quality score; higher is better.

    The score intentionally penalizes realized/expected cost, rejects/cancels,
    incomplete fills, latency, adverse selection and inadequate available
    liquidity. It is an operational diagnostic, not a profitability claim.
    """
    if not 0.0 <= available_liquidity_ratio <= 1.0:
        raise ValueError('available_liquidity_ratio must be in [0,1]')
    numeric = [
        q.quoted_spread_bps, q.effective_spread_bps, q.realized_slippage_bps,
        q.expected_slippage_bps, q.fill_ratio, q.partial_fill_ratio, q.cancel_ratio,
        q.reject_ratio, q.avg_ack_ms, q.avg_fill_ms, q.market_impact_bps,
        q.adverse_selection_bps, q.maker_ratio, available_liquidity_ratio,
    ]
    if any(x != x or x in (float('inf'), float('-inf')) for x in numeric):
        raise ValueError('execution quality values must be finite')
    penalty = 0.0
    penalty += min(20.0, max(0.0, q.quoted_spread_bps) * 0.40)
    penalty += min(15.0, abs(q.realized_slippage_bps) * 0.50)
    penalty += min(10.0, abs(q.expected_slippage_bps) * 0.25)
    penalty += min(10.0, max(0.0, q.market_impact_bps) * 0.25)
    penalty += min(10.0, max(0.0, q.adverse_selection_bps) * 0.25)
    penalty += 15.0 * max(0.0, 1.0 - q.fill_ratio)
    penalty += 5.0 * max(0.0, q.partial_fill_ratio)
    penalty += 7.5 * max(0.0, q.cancel_ratio)
    penalty += 12.5 * max(0.0, q.reject_ratio)
    penalty += min(5.0, max(0.0, q.avg_ack_ms - 250.0) / 250.0)
    penalty += min(5.0, max(0.0, q.avg_fill_ms - 1000.0) / 1000.0)
    penalty += 10.0 * (1.0 - available_liquidity_ratio)
    return max(0.0, min(100.0, 100.0 - penalty))
