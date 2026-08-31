from decimal import Decimal
from types import SimpleNamespace
import math
import pytest

from app.indicators.engine import advanced_indicators
from app.strategies.levels import TradeLevelConfig, build_long_levels, update_protective_stop
from app.backtest.analytics import performance_metrics, sensitivity_analysis
from app.strategies.catalog import STRATEGY_FAMILIES, StrategyVote, ensemble_vote
from app.backtest.validation import walk_forward_splits, purged_embargo_split, monte_carlo


def _rows(n=80):
    rows=[]
    for i in range(n):
        base=100 + i*0.15 + (i%7-3)*0.25
        rows.append({"open":base-0.1,"high":base+0.8,"low":base-0.7,"close":base,"volume":1000+(i%9)*90,"session_id":i//24})
    return rows


def test_phase109_advanced_indicator_set_is_finite_point_in_time_and_quality_labeled():
    out=advanced_indicators(_rows(),anchor_index=20)
    expected={"swing_high","swing_low","donchian_upper","donchian_lower","keltner_upper","keltner_lower","bb_kc_squeeze","anchored_vwap","session_vwap","rolling_zscore","parkinson_volatility","garman_klass_volatility","volume_poc","value_area_low","value_area_high","volume_profile_quality","trend_efficiency","choppiness"}
    assert expected <= set(out)
    assert all(math.isfinite(v) for v in out.values())
    assert out["donchian_upper"] >= out["donchian_lower"]
    assert 0 <= out["trend_efficiency"] <= 1 and 0 <= out["choppiness"] <= 100
    assert out["volume_profile_quality"] == 1
    with pytest.raises(ValueError): advanced_indicators(_rows(),anchor_index=999)


def test_phase109_volume_profile_refuses_to_claim_quality_when_data_is_insufficient():
    out=advanced_indicators(_rows(5))
    assert out["volume_profile_quality"] == 0
    assert out["volume_poc"] == pytest.approx(_rows(5)[-1]["close"])


def test_phase109_entry_stop_take_profit_trailing_and_break_even_are_machine_calculated_and_bounded():
    cfg=TradeLevelConfig(max_stop_fraction=Decimal("0.05"),take_profit_rr=(Decimal("1"),Decimal("2"),Decimal("4")))
    levels=build_long_levels(price=Decimal("100"),atr=Decimal("2"),swing_low=Decimal("96"),config=cfg)
    assert Decimal("95") <= levels.stop < levels.entry
    assert levels.risk_per_unit == levels.entry-levels.stop
    assert levels.take_profits == tuple(levels.entry+levels.risk_per_unit*x for x in cfg.take_profit_rr)
    tightened=update_protective_stop(current_stop=levels.stop,entry=levels.entry,price=Decimal("106"),atr=Decimal("2"),config=cfg)
    assert tightened >= levels.stop and tightened >= levels.entry


def test_phase109_backtest_performance_metrics_are_complete_and_consistent():
    trades=[SimpleNamespace(pnl=x,entry_time=i,exit_time=i+2) for i,x in enumerate([100,-50,80,-20,40])]
    m=performance_metrics(trades,initial_equity=10000,elapsed_years=1)
    assert m.number_of_trades == 5
    assert m.total_return == pytest.approx(0.015)
    assert m.win_rate == pytest.approx(0.6) and m.loss_rate == pytest.approx(0.4)
    assert m.average_win > 0 and m.average_loss < 0
    assert m.largest_win == 100 and m.largest_loss == -50
    assert m.average_holding_time == 2
    assert m.max_drawdown >= 0


def test_phase109_walkforward_purge_monte_carlo_and_sensitivity_are_deterministic_oos_tools():
    splits=walk_forward_splits(100,60,20)
    assert splits and set(splits[0][0]).isdisjoint(splits[0][1])
    train,test=purged_embargo_split(30,10,15,purge=2,embargo=2)
    assert set(train).isdisjoint(test) and 8 not in train and 15 not in train
    assert monte_carlo([.01,-.005,.02],100,7)==monte_carlo([.01,-.005,.02],100,7)
    assert sensitivity_analysis([3,1,2],lambda x:x*x)==[{"parameter":1,"metric":1.0},{"parameter":2,"metric":4.0},{"parameter":3,"metric":9.0}]


def test_phase109_strategy_ensemble_has_declared_families_and_requires_bounded_agreement():
    assert set(STRATEGY_FAMILIES)=={"TREND_FOLLOWING","BREAKOUT","PULLBACK","MEAN_REVERSION","MOMENTUM"}
    votes=[StrategyVote("TREND_FOLLOWING",1,.9),StrategyVote("BREAKOUT",1,.8),StrategyVote("MEAN_REVERSION",-1,.2)]
    out=ensemble_vote(votes,min_agreement=.6)
    assert out["decision"]=="BUY" and out["agreement"]>=.6
    conflict=ensemble_vote([StrategyVote("MOMENTUM",1,1),StrategyVote("MEAN_REVERSION",-1,1)])
    assert conflict["decision"]=="NO_TRADE"
