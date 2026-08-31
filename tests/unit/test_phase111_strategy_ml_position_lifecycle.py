from app.research.strategy_selection import StrategyMetrics, select_strategy
from app.research.self_learning import analyze_history
from app.research.ml_contract import ModelVersion,time_series_train_test,dataset_hash,feature_importance,population_stability_index
from app.risk.position_view import position_health


def test_phase111_strategy_selection_ranks_return_drawdown_sharpe_sortino_profit_factor_stability_and_trade_count_without_profit_guarantee():
    rows=[StrategyMetrics("A",.2,.1,1.2,1.5,1.6,.8,80),StrategyMetrics("B",.3,.4,.7,.8,1.1,.4,100)]
    out=select_strategy(rows)
    assert out["selected"]=="A" and out["guaranteed_profit"] is False and out["reason"]=="EVIDENCE_RANKING_ONLY"
    assert select_strategy([StrategyMetrics("x",1,0,5,5,5,1,2)])["selected"] is None


def test_phase111_self_learning_analyzes_history_measures_degradation_and_only_proposes_paper_validated_non_live_parameter_changes():
    out=analyze_history([-.01]*35,baseline_expectancy=0,current_threshold=.6)
    assert out["degraded"] and out["proposals"]
    p=out["proposals"][0]
    assert p.requires_paper_validation and not p.auto_promote_live and p.proposed>p.current


def test_phase111_ml_contract_has_point_in_time_training_dataset_split_versioning_importance_and_drift_detection():
    rows=[{"available_at":f"2026-01-{i:02d}","x":i} for i in range(1,11)]
    train,test=time_series_train_test(rows,train_fraction=.7)
    assert len(train)==7 and len(test)==3 and train[-1]["available_at"]<test[0]["available_at"]
    assert dataset_hash(rows)==dataset_hash(list(rows)) and len(dataset_hash(rows))==64
    v=ModelVersion("m1","features-v1",train[-1]["available_at"],dataset_hash(train))
    assert not v.approved_for_live
    imp=feature_importance({"a":2,"b":1}); assert imp[0][0]=="a" and abs(sum(x[1] for x in imp)-1)<1e-9
    assert population_stability_index([0]*20+[1]*20,[10]*40)>0


def test_phase111_position_management_exposes_unrealized_pnl_current_r_stop_and_take_profit_distances():
    out=position_health(entry=100,price=104,stop=98,take_profits=[106,110],quantity=2,fees=1)
    assert out["unrealized_pnl"]==7 and out["current_r"]==2
    assert out["distance_to_sl"]>0 and len(out["distance_to_tp"])==2 and not out["at_or_below_stop"]
