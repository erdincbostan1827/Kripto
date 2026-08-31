from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal

import pytest

from app.core.enums import OrderState
from app.exchange.mock import MockExchange
from app.exchange.models import OrderIntent, SymbolFilters
from app.execution.reconciliation import resolve_cancel_timeout
from app.execution.reservation import CapitalReservations
from app.execution.service import ExecutionService
from app.risk.state import RiskMachine


def _intent(intent_id='i1', symbol='BTCUSDT'):
    return OrderIntent(intent_id, 'a1', symbol, 'BUY', 'LIMIT', Decimal('0.01'), Decimal('60000'))


def test_concurrent_multi_symbol_reservations_never_overcommit_available_capital():
    reservations = CapitalReservations()

    def attempt(index):
        try:
            reservations.reserve(f'i{index}', '60', '100', now=1)
            return True
        except ValueError:
            return False

    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(attempt, range(20)))

    assert sum(results) == 1
    assert sum(x.amount for x in reservations.items.values()) == Decimal('60')


def test_reservation_rejects_non_positive_amount():
    reservations = CapitalReservations()
    with pytest.raises(ValueError, match='positive'):
        reservations.reserve('bad', '0', '100', now=1)


class ChangingFiltersExchange(MockExchange):
    def __init__(self):
        super().__init__()
        self.filter_reads = 0

    def get_symbol_filters(self, symbol):
        self.filter_reads += 1
        base = super().get_symbol_filters(symbol)
        if self.filter_reads >= 2:
            return SymbolFilters(
                base.tick_size,
                Decimal('0.001'),
                base.min_qty,
                base.max_qty,
                base.min_notional,
                base.max_notional,
                base.max_orders,
            )
        return base


def test_symbol_filter_change_between_validation_and_submit_fails_closed():
    exchange = ChangingFiltersExchange()
    risk = RiskMachine()
    service = ExecutionService(exchange, risk)
    with pytest.raises(PermissionError, match='metadata changed'):
        service.submit(_intent(), Decimal('60000'), Decimal('100'))
    assert risk.state.value == 'MANUAL_REVIEW_REQUIRED'
    assert not exchange.orders


def test_cancel_timeout_applies_terminal_exchange_truth():
    exchange = MockExchange()
    record = exchange.submit_order(_intent())
    record.state = OrderState.FILLED
    resolved = resolve_cancel_timeout(
        exchange=exchange,
        symbol='BTCUSDT',
        order_id=record.exchange_order_id,
        local_state='CANCEL_PENDING',
    )
    assert resolved.state == 'FILLED'
    assert resolved.action == 'APPLY_EXCHANGE_TRUTH'


def test_cancel_timeout_does_not_assume_missing_order_was_cancelled():
    resolved = resolve_cancel_timeout(
        exchange=MockExchange(),
        symbol='BTCUSDT',
        order_id='missing',
        local_state='CANCEL_PENDING',
    )
    assert resolved.state == 'UNKNOWN'
    assert resolved.action == 'MANUAL_REVIEW_REQUIRED'


def test_cancel_timeout_live_order_requires_reconcile_and_retry_not_assumed_cancelled():
    exchange = MockExchange()
    record = exchange.submit_order(_intent())
    resolved = resolve_cancel_timeout(
        exchange=exchange,
        symbol='BTCUSDT',
        order_id=record.exchange_order_id,
        local_state='CANCEL_PENDING',
    )
    assert resolved.state == 'ACKNOWLEDGED'
    assert resolved.action == 'RECONCILE_AND_RETRY_CANCEL'
