from decimal import Decimal
import pytest

from app.core.config import Settings
from app.core.enums import MarketType
from app.core.money import normalize_price, normalize_quantity
from app.exchange.models import OrderIntent
from app.execution.pretrade import validate_spot_sell_balance


def test_financial_rounding_is_directional_not_builtin_round():
    assert normalize_price(Decimal('10.019'),Decimal('0.01'),'BUY')==Decimal('10.01')
    assert normalize_price(Decimal('10.011'),Decimal('0.01'),'SELL')==Decimal('10.02')
    assert normalize_quantity(Decimal('1.239'),Decimal('0.01'))==Decimal('1.23')


def test_safe_default_market_type_is_spot():
    assert Settings().market_type==MarketType.SPOT


def test_spot_sell_cannot_exceed_available_base_balance():
    intent=OrderIntent('spot-sell','a','BTCUSDT','SELL','MARKET',Decimal('1.1'),market_type=MarketType.SPOT)
    with pytest.raises(PermissionError,match='exceeds'):
        validate_spot_sell_balance(intent,Decimal('1.0'))
    validate_spot_sell_balance(intent,Decimal('1.1'))


def test_spot_sell_requires_balance_context_fail_closed():
    intent=OrderIntent('spot-sell','a','BTCUSDT','SELL','MARKET',Decimal('0.1'),market_type=MarketType.SPOT)
    with pytest.raises(PermissionError,match='requires'):
        validate_spot_sell_balance(intent,None)


def test_execution_service_enforces_spot_sell_balance_before_exchange_side_effect():
    from app.exchange.mock import MockExchange
    from app.execution.service import ExecutionService
    from app.risk.state import RiskMachine
    exchange=MockExchange(); service=ExecutionService(exchange,RiskMachine())
    intent=OrderIntent('sell-live-safe','a','BTCUSDT','SELL','MARKET',Decimal('0.2'),market_type=MarketType.SPOT)
    with pytest.raises(PermissionError):
        service.submit(intent,Decimal('60000'),Decimal('100'),current_available_base_qty=Decimal('0.1'))
    assert not exchange.orders
