from datetime import datetime,timezone,timedelta
from pathlib import Path
from decimal import Decimal
from app.indicators.engine import indicators
from app.signals.engine import decide
from app.risk.engine import size_position
from app.backtest.execution_model import next_bar_market_fill,conservative_exit_long


def _rows(n=250):
    t=datetime(2025,1,1,tzinfo=timezone.utc); out=[]
    for i in range(n):
        p=100+i*.2
        out.append({'open_time':t+timedelta(hours=i),'close_time':t+timedelta(hours=i+1),'open':p,'high':p+1,'low':p-1,'close':p+.1,'volume':100+i,'closed':True})
    return out


def test_signal_stop_take_profit_and_risk_reward_calculation_are_explicit():
    f=indicators(_rows()); f['price']=float(_rows()[-1]['close']); d=decide(f,'BULLISH_TREND','2026-01-01T00:00:00Z')
    assert d.entry is not None and d.stop_loss is not None and len(d.take_profits)==3
    assert d.stop_loss<d.entry<d.take_profits[0]<d.take_profits[1]<d.take_profits[2]
    assert d.risk_reward is not None and d.risk_reward>=Decimal('2')


def test_position_risk_calculation_returns_positive_bounded_quantity():
    q=size_position('10000','100','95','0.001','0.0025')
    assert q>0 and q<Decimal('10000')/Decimal('100')


def test_backtest_fee_slippage_future_leakage_and_stop_execution_contracts():
    market=next_bar_market_fill('BUY',Decimal('101'),Decimal('10'))
    stop=conservative_exit_long(bar_open=Decimal('90'),bar_high=Decimal('96'),bar_low=Decimal('88'),stop=Decimal('95'),tp=Decimal('110'),slippage_bps=Decimal('10'))
    assert market.reason=='NEXT_BAR_MARKET' and market.price>Decimal('101')
    assert stop.reason=='STOP_GAP_THROUGH' and stop.price<Decimal('90')


def test_readme_and_operator_docs_cover_install_modes_risk_backup_and_recovery():
    root=Path('.')
    readme=(root/'README.md').read_text(encoding='utf-8')
    required=['## Canonical architecture','## Installation','## Product modes','## Risk and execution','## PAPER / research / backtest','## Docker / deployment / backup','## Known blockers before PROD LIVE']
    assert all(x in readme for x in required)
    for p in ['ARCHITECTURE.md','docs/USER_GUIDE.md','docs/TROUBLESHOOTING.md','docs/DISASTER_RECOVERY.md','BACKUP_RESTORE_DRILL.md']:
        assert (root/p).is_file() and (root/p).stat().st_size>100
    assert 'PAPER' in readme and 'TESTNET' in readme and 'LIVE' in readme and 'LIVE remains disabled' in readme
