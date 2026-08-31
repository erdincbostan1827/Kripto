from __future__ import annotations

from dataclasses import asdict, dataclass
from decimal import Decimal
from enum import Enum
from typing import Any

from app.core.enums import MarketType
from app.exchange.models import OrderIntent


class PositionSide(str, Enum):
    LONG = "LONG"
    SHORT = "SHORT"


class TradeAction(str, Enum):
    INCREASE_LONG = "INCREASE_LONG"
    REDUCE_LONG_OR_EXIT = "REDUCE_LONG_OR_EXIT"
    INCREASE_SHORT = "INCREASE_SHORT"
    REDUCE_SHORT_OR_EXIT = "REDUCE_SHORT_OR_EXIT"
    NO_ACTION = "NO_ACTION"


@dataclass(frozen=True)
class SignalContext:
    signal: str
    market_type: MarketType
    position_side: PositionSide
    current_position_qty: Decimal

    def __post_init__(self) -> None:
        if self.signal not in {"BUY", "SELL"}:
            raise ValueError("signal must be BUY or SELL")
        if self.current_position_qty < 0:
            raise ValueError("current_position_qty must be non-negative absolute quantity")


@dataclass(frozen=True)
class StrategySpec:
    strategy_id: str
    strategy_version: str
    hypothesis: str
    supported_market_types: tuple[str, ...]
    supported_symbols: tuple[str, ...]
    allowed_direction: tuple[str, ...]
    required_timeframes: tuple[str, ...]
    required_features: tuple[str, ...]
    warmup: int
    valid_regimes: tuple[str, ...]
    invalid_regimes: tuple[str, ...]
    entry_rule: str
    confirmation_rule: str
    invalidation_rule: str
    exit_rule: str
    stop_rule: str
    take_profit_rule: str
    max_holding_time_seconds: int
    cooldown_seconds: int
    order_policy: dict[str, Any]
    position_sizing_policy: dict[str, Any]
    risk_limits: dict[str, Any]
    assumptions: tuple[str, ...]
    known_failure_modes: tuple[str, ...]
    allow_short: bool = False
    short_validation: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        required_strings = (
            "strategy_id",
            "strategy_version",
            "hypothesis",
            "entry_rule",
            "confirmation_rule",
            "invalidation_rule",
            "exit_rule",
            "stop_rule",
            "take_profit_rule",
        )
        if any(not str(getattr(self, name)).strip() for name in required_strings):
            raise ValueError("strategy specification contains empty required text")
        required_sequences = (
            self.supported_market_types,
            self.supported_symbols,
            self.allowed_direction,
            self.required_timeframes,
            self.required_features,
            self.assumptions,
            self.known_failure_modes,
        )
        if any(not values for values in required_sequences):
            raise ValueError("strategy specification contains empty required collection")
        if not set(self.supported_market_types) <= {MarketType.SPOT.value, MarketType.PERPETUAL.value}:
            raise ValueError("unsupported market type")
        if not set(self.allowed_direction) <= {PositionSide.LONG.value, PositionSide.SHORT.value}:
            raise ValueError("allowed_direction must contain only LONG/SHORT")
        if set(self.valid_regimes) & set(self.invalid_regimes):
            raise ValueError("valid and invalid regimes cannot overlap")
        if self.warmup < 1 or self.max_holding_time_seconds < 1 or self.cooldown_seconds < 0:
            raise ValueError("warmup/holding/cooldown values are invalid")
        if not self.order_policy or not self.position_sizing_policy or not self.risk_limits:
            raise ValueError("order, sizing and risk policies are required")
        if PositionSide.SHORT.value in self.allowed_direction and not self.allow_short:
            raise ValueError("SHORT direction requires allow_short=true")
        if self.allow_short:
            required_short = {"max_short_exposure", "liquidation_buffer"}
            if not isinstance(self.short_validation, dict) or not required_short <= set(self.short_validation):
                raise ValueError("short trading requires separate short_validation limits")
            if any(float(self.short_validation[key]) <= 0 for key in required_short):
                raise ValueError("short_validation limits must be positive")

    def to_machine_readable(self) -> dict[str, Any]:
        return asdict(self)

    def to_markdown(self) -> str:
        rows = self.to_machine_readable()
        lines = [f"# StrategySpec: {self.strategy_id}", ""]
        for key, value in rows.items():
            lines.append(f"- **{key}**: {value}")
        return "\n".join(lines) + "\n"

    def interpret_signal(self, context: SignalContext) -> TradeAction:
        if context.market_type.value not in self.supported_market_types:
            raise PermissionError("market type not supported by strategy")
        if context.market_type == MarketType.SPOT:
            if context.position_side != PositionSide.LONG:
                raise PermissionError("SPOT position side must be LONG inventory")
            if context.signal == "BUY":
                return TradeAction.INCREASE_LONG
            return TradeAction.REDUCE_LONG_OR_EXIT if context.current_position_qty > 0 else TradeAction.NO_ACTION

        if context.position_side == PositionSide.LONG:
            if context.signal == "BUY":
                return TradeAction.INCREASE_LONG
            return TradeAction.REDUCE_LONG_OR_EXIT if context.current_position_qty > 0 else TradeAction.NO_ACTION

        if not self.allow_short:
            raise PermissionError("short trading is disabled")
        if context.signal == "SELL":
            return TradeAction.INCREASE_SHORT
        return TradeAction.REDUCE_SHORT_OR_EXIT if context.current_position_qty > 0 else TradeAction.NO_ACTION


@dataclass(frozen=True)
class SignalDecision:
    strategy_id: str
    symbol: str
    context: SignalContext
    action: TradeAction


@dataclass(frozen=True)
class RiskApprovedDecision:
    signal: SignalDecision
    approved: bool
    reason: str


class StrategyDecisionFlow:
    def __init__(self, spec: StrategySpec):
        self.spec = spec

    def signal(self, *, symbol: str, context: SignalContext) -> SignalDecision:
        if symbol not in self.spec.supported_symbols:
            raise PermissionError("symbol not supported by strategy")
        return SignalDecision(self.spec.strategy_id, symbol, context, self.spec.interpret_signal(context))

    @staticmethod
    def approve_risk(signal: SignalDecision, *, approved: bool, reason: str) -> RiskApprovedDecision:
        if not reason.strip():
            raise ValueError("risk decision reason is required")
        return RiskApprovedDecision(signal=signal, approved=bool(approved), reason=reason)

    @staticmethod
    def to_order_intent(
        decision: RiskApprovedDecision,
        *,
        intent_id: str,
        account_id: str,
        quantity: Decimal,
        order_type: str = "MARKET",
    ) -> OrderIntent:
        if not decision.approved:
            raise PermissionError("Signal -> RiskApproved -> OrderIntent transition requires approval")
        if quantity <= 0:
            raise ValueError("quantity must be positive")
        action = decision.signal.action
        if action == TradeAction.NO_ACTION:
            raise PermissionError("NO_ACTION cannot become OrderIntent")
        side = "BUY" if action in {TradeAction.INCREASE_LONG, TradeAction.REDUCE_SHORT_OR_EXIT} else "SELL"
        reduce_only = decision.signal.context.market_type == MarketType.PERPETUAL and action in {
            TradeAction.REDUCE_LONG_OR_EXIT,
            TradeAction.REDUCE_SHORT_OR_EXIT,
        }
        return OrderIntent(
            intent_id=intent_id,
            account_id=account_id,
            symbol=decision.signal.symbol,
            side=side,
            order_type=order_type,
            quantity=quantity,
            market_type=decision.signal.context.market_type,
            strategy_id=decision.signal.strategy_id,
            reduce_only=reduce_only,
            client_order_id=intent_id,
        )
