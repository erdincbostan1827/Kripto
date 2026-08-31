import pytest
from app.strategies.lifecycle import StrategyLifecycle
from app.strategies.health import StrategyHealthMonitor
from app.signals.calibration import calibrate
from app.backtest.benchmarks import *
from app.backtest.dataset import manifest,verify_manifest
from app.research.registry import ResearchRegistry,ResearchTrial
from app.research.shadow import LiveShadow
from app.risk.config_safety import assess_change
from app.risk.live_ramp import LiveRamp
from app.risk.attribution import PnLAttribution,implementation_shortfall

def test_strategy_promotion_sequential():
 s=StrategyLifecycle('s'); assert s.promote('BACKTEST_VALIDATED',{'backtest':True})=='BACKTEST_VALIDATED'; assert s.promote('OOS_VALIDATED',{'oos':True})=='OOS_VALIDATED'
def test_strategy_cannot_skip():
 with pytest.raises(PermissionError): StrategyLifecycle('s').promote('OOS_VALIDATED',{'oos':True})
def test_live_approval_human():
 s=StrategyLifecycle('s','SHADOW_VALIDATED')
 with pytest.raises(PermissionError): s.promote('LIVE_APPROVED',{'final_profitability':True},False)
def test_health_threshold_configurable():
 base=[.01,-.01,.012,-.008]*10; current=[-.03]*40; assert StrategyHealthMonitor(z_threshold=1,min_samples=30).assess(base,current,1,1).degraded
def test_health_insufficient_sample_not_promoted(): assert 'INSUFFICIENT_SAMPLE' in StrategyHealthMonitor(min_samples=30).assess([1],[1],1,1).reasons
def test_calibration_report():
 r=calibrate([.1,.8,.9,.2],[0,1,1,0]); assert r.sample_count==4 and 0<=r.brier_score<=1 and r.buckets
def test_benchmarks():
 p=[100,105,110]; assert buy_and_hold(p)==pytest.approx(.1) and cash_baseline()==0 and equal_weight_asset_returns({'a':p})==pytest.approx(.1)
def test_dataset_manifest_detects_change():
 rows=[{'t':1,'p':2}]; m=manifest('d','p',['BTC'],'a','b','u',{},'c',rows); assert verify_manifest(m,rows) and not verify_manifest(m,[{'t':1,'p':3}])
def test_research_registry_keeps_failures():
 r=ResearchRegistry(); r.append(ResearchTrial('1','u','s',{},(),(),('a','b'),('c','d'),'sharpe',{'accepted':False})); assert len(r.failed())==1
def test_research_duplicate_trial_rejected():
 r=ResearchRegistry(); t=ResearchTrial('1','u','s',{},(),(),('a','b'),('c','d'),'sharpe',{}) ;r.append(t)
 with pytest.raises(ValueError):r.append(t)
def test_live_shadow_never_orders(): assert LiveShadow().compare('BUY','SELL').divergence and not LiveShadow().compare('BUY','SELL').real_order_allowed
def test_config_risk_increase_detected(): assert assess_change({'risk_per_trade':.001},{'risk_per_trade':.01}).risk_increasing
def test_config_hash_changes(): assert assess_change({'a':1},{'a':2}).old_hash!=assess_change({'a':1},{'a':2}).new_hash
def test_live_ramp_requires_human():
 e={k:True for k in ('reconciliation','critical_incidents_clear','protective_success','slippage_bound','shadow_divergence_bound','expectancy_acceptable','drawdown_bound','effective_sample','multiple_conditions','strategy_healthy')}
 with pytest.raises(PermissionError): LiveRamp().increase(e,False)
def test_live_ramp_and_decrease():
 e={k:True for k in ('reconciliation','critical_incidents_clear','protective_success','slippage_bound','shadow_divergence_bound','expectancy_acceptable','drawdown_bound','effective_sample','multiple_conditions','strategy_healthy')}; r=LiveRamp(); assert r.increase(e,True)=='LIVE_STAGE_1'; assert r.decrease()=='LIVE_STAGE_0'
def test_attribution_total(): assert PnLAttribution(10,1,1,1,1,1,0,0,0,0).total==9
def test_implementation_shortfall(): assert implementation_shortfall(100,101,'BUY')==.01
