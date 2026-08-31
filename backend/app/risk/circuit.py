from __future__ import annotations
from dataclasses import dataclass,field
from app.core.enums import RiskState
@dataclass
class CircuitBreaker:
    risk_state:RiskState=RiskState.NORMAL; reasons:list[str]=field(default_factory=list)
    def evaluate(self,**checks):
        fatal={'database_ok','redis_ok','exchange_ok','clock_ok','private_stream_ok','data_fresh','balance_consistent','protective_orders_ok','duplicate_order_ok','spread_ok','volatility_ok','daily_loss_ok','drawdown_ok','order_rejection_ok'}
        failed=[k for k,v in checks.items() if not v]
        if any(k in fatal for k in failed): self.risk_state=RiskState.HALTED
        elif failed: self.risk_state=RiskState.RESTRICTED
        else: self.risk_state=RiskState.NORMAL
        self.reasons=failed; return self.risk_state
