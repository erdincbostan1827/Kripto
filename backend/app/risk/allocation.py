from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

ZERO = Decimal("0")
ONE = Decimal("1")


@dataclass(frozen=True)
class AllocationCandidate:
    symbol: str
    requested_notional: Decimal
    expected_edge_bps: Decimal
    stop_risk_fraction: Decimal
    volatility_fraction: Decimal
    liquidity_score: Decimal
    correlation_penalty: Decimal
    strategy_health: Decimal
    drawdown_multiplier: Decimal
    regime_multiplier: Decimal
    quote_asset_multiplier: Decimal


@dataclass(frozen=True)
class AllocationState:
    account_equity: Decimal
    free_cash: Decimal
    portfolio_heat_fraction: Decimal
    max_portfolio_heat_fraction: Decimal
    risk_budget_remaining: Decimal
    open_order_reserved: Decimal = ZERO
    reserve_fraction: Decimal = Decimal("0.15")
    cost_buffer_fraction: Decimal = Decimal("0.005")
    max_cycle_allocation_fraction: Decimal = Decimal("0.20")
    max_single_candidate_fraction: Decimal = Decimal("0.10")


@dataclass(frozen=True)
class AllocationDecision:
    symbol: str
    allocated_notional: Decimal
    expected_stop_loss: Decimal
    score: Decimal
    reason: str


class CapitalAllocator:
    @staticmethod
    def _clamp01(value: Decimal) -> Decimal:
        return min(ONE, max(ZERO, value))

    @classmethod
    def _score(cls, candidate: AllocationCandidate) -> Decimal:
        if candidate.expected_edge_bps <= ZERO or candidate.stop_risk_fraction <= ZERO:
            return ZERO
        if candidate.requested_notional <= ZERO:
            return ZERO
        liquidity = cls._clamp01(candidate.liquidity_score)
        correlation = ONE - cls._clamp01(candidate.correlation_penalty)
        health = cls._clamp01(candidate.strategy_health)
        drawdown = cls._clamp01(candidate.drawdown_multiplier)
        regime = cls._clamp01(candidate.regime_multiplier)
        quote = cls._clamp01(candidate.quote_asset_multiplier)
        volatility_penalty = ONE + max(ZERO, candidate.volatility_fraction)
        return (
            candidate.expected_edge_bps
            * liquidity
            * correlation
            * health
            * drawdown
            * regime
            * quote
            / volatility_penalty
        )

    @staticmethod
    def _validate_state(state: AllocationState) -> None:
        numeric = [
            state.account_equity,
            state.free_cash,
            state.portfolio_heat_fraction,
            state.max_portfolio_heat_fraction,
            state.risk_budget_remaining,
            state.open_order_reserved,
            state.reserve_fraction,
            state.cost_buffer_fraction,
            state.max_cycle_allocation_fraction,
            state.max_single_candidate_fraction,
        ]
        if any(not value.is_finite() for value in numeric):
            raise ValueError("allocation state must contain finite decimal values")
        if state.account_equity <= ZERO or state.free_cash < ZERO or state.risk_budget_remaining < ZERO:
            raise ValueError("invalid account allocation state")
        if state.portfolio_heat_fraction < ZERO or state.max_portfolio_heat_fraction < ZERO:
            raise ValueError("portfolio heat cannot be negative")
        for fraction in (
            state.reserve_fraction,
            state.cost_buffer_fraction,
            state.max_cycle_allocation_fraction,
            state.max_single_candidate_fraction,
        ):
            if fraction < ZERO or fraction > ONE:
                raise ValueError("allocation fractions must be within [0, 1]")

    @classmethod
    def allocate_cycle(
        cls,
        state: AllocationState,
        candidates: list[AllocationCandidate],
    ) -> list[AllocationDecision]:
        cls._validate_state(state)
        reserve = state.account_equity * state.reserve_fraction
        cost_buffer = state.account_equity * state.cost_buffer_fraction
        liquid_budget = max(ZERO, state.free_cash - state.open_order_reserved - reserve - cost_buffer)
        heat_capacity = max(
            ZERO,
            state.account_equity * (state.max_portfolio_heat_fraction - state.portfolio_heat_fraction),
        )
        cycle_cap = state.account_equity * state.max_cycle_allocation_fraction
        remaining_notional = min(liquid_budget, cycle_cap)
        remaining_risk = min(state.risk_budget_remaining, heat_capacity)
        single_cap = state.account_equity * state.max_single_candidate_fraction

        ranked = sorted(candidates, key=lambda item: (-cls._score(item), item.symbol))
        decisions: list[AllocationDecision] = []
        for candidate in ranked:
            score = cls._score(candidate)
            if score <= ZERO:
                decisions.append(AllocationDecision(candidate.symbol, ZERO, ZERO, score, "NO_POSITIVE_ALLOCATABLE_EDGE"))
                continue
            if candidate.stop_risk_fraction <= ZERO:
                decisions.append(AllocationDecision(candidate.symbol, ZERO, ZERO, score, "INVALID_STOP_RISK"))
                continue
            if remaining_notional <= ZERO or remaining_risk <= ZERO:
                decisions.append(AllocationDecision(candidate.symbol, ZERO, ZERO, score, "CYCLE_OR_RISK_BUDGET_EXHAUSTED"))
                continue

            max_by_risk = remaining_risk / candidate.stop_risk_fraction
            allocation = min(candidate.requested_notional, single_cap, remaining_notional, max_by_risk)
            if allocation <= ZERO:
                decisions.append(AllocationDecision(candidate.symbol, ZERO, ZERO, score, "NO_AVAILABLE_CAPITAL"))
                continue
            stop_loss = allocation * candidate.stop_risk_fraction
            decisions.append(AllocationDecision(candidate.symbol, allocation, stop_loss, score, "ALLOCATED"))
            remaining_notional -= allocation
            remaining_risk -= stop_loss
        return decisions


class ConcurrentAllocationCoordinator:
    """Serialize candidate reconciliation against shared account capital.

    Each cycle consumes from a shared notional/risk envelope until reset. This
    prevents two scanner workers from independently allocating the same capital
    after ranking candidates from the same account snapshot.
    """

    def __init__(self):
        import threading
        self._lock = threading.RLock()
        self._cycle_id: str | None = None
        self._allocated_notional = ZERO
        self._allocated_risk = ZERO

    def begin_cycle(self, cycle_id: str) -> None:
        if not cycle_id:
            raise ValueError('cycle_id required')
        with self._lock:
            if self._cycle_id != cycle_id:
                self._cycle_id = cycle_id
                self._allocated_notional = ZERO
                self._allocated_risk = ZERO

    def reconcile_and_allocate(
        self,
        cycle_id: str,
        state: AllocationState,
        candidates: list[AllocationCandidate],
    ) -> list[AllocationDecision]:
        with self._lock:
            self.begin_cycle(cycle_id)
            adjusted = AllocationState(
                account_equity=state.account_equity,
                free_cash=max(ZERO, state.free_cash - self._allocated_notional),
                portfolio_heat_fraction=state.portfolio_heat_fraction,
                max_portfolio_heat_fraction=state.max_portfolio_heat_fraction,
                risk_budget_remaining=max(ZERO, state.risk_budget_remaining - self._allocated_risk),
                open_order_reserved=state.open_order_reserved,
                reserve_fraction=state.reserve_fraction,
                cost_buffer_fraction=state.cost_buffer_fraction,
                max_cycle_allocation_fraction=state.max_cycle_allocation_fraction,
                max_single_candidate_fraction=state.max_single_candidate_fraction,
            )
            decisions = CapitalAllocator.allocate_cycle(adjusted, candidates)
            self._allocated_notional += sum((d.allocated_notional for d in decisions), ZERO)
            self._allocated_risk += sum((d.expected_stop_loss for d in decisions), ZERO)
            return decisions

    def telemetry(self) -> dict[str, Decimal | str | None]:
        with self._lock:
            return {
                'cycle_id': self._cycle_id,
                'allocated_notional': self._allocated_notional,
                'allocated_risk': self._allocated_risk,
            }
