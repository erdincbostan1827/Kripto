from __future__ import annotations
from dataclasses import dataclass
@dataclass(frozen=True)
class Candidate:
    symbol:str; score:float; confidence:float; net_edge_bps:float; risk_blocked:bool=False

def rank_candidates(items:list[Candidate],limit=10): return sorted([x for x in items if not x.risk_blocked and x.net_edge_bps>0],key=lambda x:(-x.score,-x.confidence,-x.net_edge_bps,x.symbol))[:limit]
def market_breadth(states:dict[str,str]):
    n=len(states) or 1; bull=sum(v=='BULLISH_TREND' for v in states.values()); bear=sum(v=='BEARISH_TREND' for v in states.values()); return {'bullish_pct':bull/n,'bearish_pct':bear/n,'count':len(states)}


def scanner_signal(items:list[Candidate]):
    """Return an explicit fail-closed decision when no tradable candidate survives."""
    from app.core.enums import Signal
    ranked=rank_candidates(items)
    return (Signal.NO_TRADE, None) if not ranked else (Signal.WATCH, ranked[0])

@dataclass(frozen=True)
class ScannerCycleTelemetry:
    universe_size: int
    eligible_size: int
    candidates_total: int
    refresh_failures: int
    cycle_duration_seconds: float
    snapshot_id: str
    completed_at: float
    excluded_size: int = 0
    stale_symbols: int = 0


class DynamicUniverseScanner:
    """Deterministic dynamic-universe scan with explicit health telemetry."""

    def __init__(self, configured_max_symbols: int = 200):
        if configured_max_symbols <= 0:
            raise ValueError('configured_max_symbols must be positive')
        self.configured_max_symbols = configured_max_symbols
        self.last_cycle: ScannerCycleTelemetry | None = None
        self.refresh_failures = 0

    def discover(
        self,
        states: list[object],
        *,
        snapshot_id: str,
        now: float,
        started_at: float,
        allowlist: set[str] | None = None,
        blocklist: set[str] | None = None,
        approved_quotes: tuple[str, ...] = ('USDT', 'USDC'),
    ) -> tuple[list[str], ScannerCycleTelemetry]:
        from app.universe.manager import eligibility

        if now < started_at:
            raise ValueError('monotonic clock moved backwards')
        allow = {x.upper() for x in allowlist} if allowlist else None
        block = {x.upper() for x in (blocklist or set())}
        quotes = tuple(q.upper() for q in approved_quotes)
        eligible_symbols: list[str] = []
        failures = 0
        excluded = 0
        stale = 0
        for state in states:
            try:
                symbol = str(state.symbol).upper()
                ok, reasons = eligibility(state)
            except (AttributeError, TypeError, ValueError):
                failures += 1
                continue
            if not getattr(state, 'data_fresh', True):
                stale += 1
            policy_ok = (allow is None or symbol in allow) and symbol not in block and any(symbol.endswith(q) for q in quotes)
            if ok and policy_ok:
                eligible_symbols.append(symbol)
            else:
                excluded += 1
        eligible_symbols = sorted(set(eligible_symbols))[: self.configured_max_symbols]
        self.refresh_failures += failures
        telemetry = ScannerCycleTelemetry(
            universe_size=len(states),
            eligible_size=len(eligible_symbols),
            candidates_total=len(eligible_symbols),
            refresh_failures=failures,
            cycle_duration_seconds=float(now - started_at),
            snapshot_id=snapshot_id,
            completed_at=float(now),
            excluded_size=excluded,
            stale_symbols=stale,
        )
        self.last_cycle = telemetry
        return eligible_symbols, telemetry

    def healthy(self, *, now: float, max_cycle_age_seconds: float) -> bool:
        if max_cycle_age_seconds <= 0:
            raise ValueError('max_cycle_age_seconds must be positive')
        if self.last_cycle is None:
            return False
        if now < self.last_cycle.completed_at:
            return False
        return self.last_cycle.refresh_failures == 0 and now - self.last_cycle.completed_at <= max_cycle_age_seconds
