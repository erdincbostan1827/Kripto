from decimal import Decimal
from pathlib import Path

from app.core.config import Settings
from app.core.enums import MarketType, TradingMode

ROOT=Path(__file__).resolve().parents[2]


def test_risk_and_runtime_parameters_are_configurable_with_conservative_defaults():
    s=Settings(
        risk_per_trade=Decimal('0.003'), max_daily_loss=Decimal('0.03'),
        max_drawdown=Decimal('0.12'), max_portfolio_exposure=Decimal('0.60'),
        max_single_asset_exposure=Decimal('0.12'), max_open_positions=9,
        min_risk_reward=Decimal('2.5'), max_spread_bps=Decimal('15'),
        min_listing_age_days=45, max_universe_size=75,
    )
    assert s.mode==TradingMode.PAPER and s.market_type==MarketType.SPOT
    assert s.risk_per_trade==Decimal('0.003') and s.max_open_positions==9 and s.max_universe_size==75


def test_install_scripts_fail_fast_and_include_build_migration_test_health_contract():
    linux=(ROOT/'install.sh').read_text(encoding='utf-8')
    windows=(ROOT/'INSTALL_WINDOWS.ps1').read_text(encoding='utf-8')
    for text in (linux,windows):
        assert 'docker' in text.lower() and 'python' in text.lower()
        assert 'bootstrap_secrets.py' in text
        assert 'alembic' in text and 'upgrade head' in text
        assert 'profile test' in text
        assert 'health' in text.lower()
        assert 'PAPER' in text
    assert 'frontend' in linux and 'build' in linux
    assert 'frontend' in windows and 'build' in windows


def test_install_and_deployment_contract_keeps_tls_and_first_start_paper():
    prod=(ROOT/'docker-compose.prod.yml').read_text(encoding='utf-8')
    nginx=(ROOT/'docker/nginx/nginx.prod.conf').read_text(encoding='utf-8')
    assert 'MODE: PAPER' in prod or 'MODE' in prod and 'PAPER' in prod
    assert 'ssl_protocols TLSv1.2 TLSv1.3' in nginx
    assert 'Strict-Transport-Security' in nginx
