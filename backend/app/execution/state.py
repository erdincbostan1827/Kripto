from __future__ import annotations
from app.core.enums import OrderState
ALLOWED={
 OrderState.CREATED:{OrderState.SUBMITTED,OrderState.REJECTED,OrderState.FAILED},
 OrderState.SUBMITTED:{OrderState.ACKNOWLEDGED,OrderState.PARTIALLY_FILLED,OrderState.FILLED,OrderState.REJECTED,OrderState.FAILED,OrderState.UNKNOWN},
 OrderState.ACKNOWLEDGED:{OrderState.PARTIALLY_FILLED,OrderState.FILLED,OrderState.CANCEL_PENDING,OrderState.CANCELLED,OrderState.REJECTED,OrderState.UNKNOWN},
 OrderState.PARTIALLY_FILLED:{OrderState.PARTIALLY_FILLED,OrderState.FILLED,OrderState.CANCEL_PENDING,OrderState.CANCELLED,OrderState.UNKNOWN},
 OrderState.CANCEL_PENDING:{OrderState.CANCELLED,OrderState.PARTIALLY_FILLED,OrderState.FILLED,OrderState.UNKNOWN},
 OrderState.UNKNOWN:{OrderState.ACKNOWLEDGED,OrderState.PARTIALLY_FILLED,OrderState.FILLED,OrderState.CANCELLED,OrderState.REJECTED,OrderState.FAILED},
}
def transition(current,new):
    if current==new: return new
    if new not in ALLOWED.get(current,set()): raise ValueError(f'illegal order transition {current}->{new}')
    return new
