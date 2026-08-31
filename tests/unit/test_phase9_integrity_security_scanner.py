from decimal import Decimal
from types import SimpleNamespace
import pytest

from app.execution.phase9 import account_net_positions, prevent_self_trade
from app.core.secret_boundary import mask_secret, redact_mapping, validate_secret_bootstrap
from app.universe.ranking import RankedCandidate, rank_with_quarantine


def test_account_level_net_position_aggregates_all_sources():
    r=account_net_positions({'BTCUSDT':Decimal('1'),'ETHUSDT':Decimal('2')},{'BTCUSDT':Decimal('-0.25')},{'ETHUSDT':Decimal('-2')})
    assert r=={'BTCUSDT':Decimal('0.75')}


def test_self_trade_prevention_blocks_crossing_platform_order():
    open_order=SimpleNamespace(symbol='BTCUSDT',side='SELL',price=Decimal('100'))
    d=prevent_self_trade(symbol='BTCUSDT',incoming_side='BUY',incoming_price=Decimal('101'),open_orders=[open_order])
    assert not d.allowed and 'CROSS' in d.reason


def test_self_trade_prevention_allows_non_crossing_order():
    open_order=SimpleNamespace(symbol='BTCUSDT',side='SELL',price=Decimal('105'))
    assert prevent_self_trade(symbol='BTCUSDT',incoming_side='BUY',incoming_price=Decimal('100'),open_orders=[open_order]).allowed


def test_secret_masking_never_echoes_plain_secret():
    raw='sk-super-secret-value'
    masked=mask_secret(raw)
    assert raw not in masked and masked.startswith('sk') and masked.endswith('ue')
    red=redact_mapping({'api_key':raw,'name':'binance'})
    assert red['api_key']!=raw and red['name']=='binance'


def test_production_secret_bootstrap_rejects_missing_mock_and_default_secret():
    bad=validate_secret_bootstrap({'ALLOW_MOCK':'1','API_KEY':'changeme'},production=True)
    assert not bad.valid and 'APP_SECRET_KEY_REQUIRED' in bad.errors and 'MOCK_FORBIDDEN_IN_PRODUCTION' in bad.errors
    good=validate_secret_bootstrap({'ALLOW_MOCK':'0','APP_SECRET_KEY':'strong-random-value'},production=True)
    assert good.valid


def test_scanner_ranking_applies_listing_quarantine_stale_and_risk_filters():
    items=[
        RankedCandidate('NEWUSDT',99,99,100,1),
        RankedCandidate('STALEUSDT',98,99,100,100,data_fresh=False),
        RankedCandidate('BLOCKUSDT',97,99,100,100,risk_blocked=True),
        RankedCandidate('BTCUSDT',90,80,30,100),
        RankedCandidate('ETHUSDT',90,70,40,100),
    ]
    ranked=rank_with_quarantine(items,min_listing_age_hours=24)
    assert [x.symbol for x in ranked]==['BTCUSDT','ETHUSDT']
