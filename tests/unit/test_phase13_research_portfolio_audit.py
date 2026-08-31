from decimal import Decimal
from datetime import date,timedelta
import numpy as np
import pytest
from app.research.validation import validate_research, holm_bonferroni_alpha
from app.signals.confidence import ConfidenceCalibrator
from app.risk.correlation import build_correlation_snapshot, concentration_breaches
from app.audit.checkpoint import create_checkpoint,verify_checkpoint
from app.api.versioning import ApiVersionPolicy,ApiVersionRegistry,DeprecationNotice


def profitable(n=80,base=.004): return [base + ((i%5)-2)*.0002 for i in range(n)]

def test_advanced_research_validation_covers_oos_walkforward_stresses_regimes_psr_dsr_bootstrap_and_multiple_testing():
    oos=profitable(); bench=[.0002]*len(oos)
    r=validate_research(in_sample_returns=profitable(100,.005),out_of_sample_returns=oos,walk_forward_returns=[.002,.003,.004],benchmark_returns=bench,
      fee_scenarios={'base':oos,'2x_fee':[x-.0003 for x in oos]},slippage_scenarios={'base':oos,'2x_slip':[x-.0004 for x in oos]},latency_scenarios={'0ms':oos,'500ms':[x-.0005 for x in oos]},parameter_scenarios={'-10%':[x-.0002 for x in oos],'+10%':[x-.0001 for x in oos]},regime_returns={'bull':profitable(20), 'bear':profitable(20,.002), 'range':profitable(20,.0015)},n_trials=10,min_psr=.5,min_dsr=.5)
    assert r.accepted and r.out_of_sample_return>r.benchmark_excess_return>0
    assert r.probabilistic_sharpe_ratio>=.5 and r.deflated_sharpe_ratio>=.5
    assert r.bootstrap_ci95[0]>0 and r.multiple_testing_adjusted_alpha==pytest.approx(.005)

def test_research_validation_rejects_weak_or_incomplete_evidence():
    weak=[-.01,.005]*20
    r=validate_research(in_sample_returns=weak,out_of_sample_returns=weak,walk_forward_returns=[-.01],benchmark_returns=[0]*40,
      fee_scenarios={'stress':weak},slippage_scenarios={'stress':weak},latency_scenarios={'stress':weak},parameter_scenarios={'stress':weak},regime_returns={'bull':weak},n_trials=100,min_psr=.99,min_dsr=.99)
    assert not r.accepted and 'MISSING_REGIME_BEAR' in r.rejection_reasons and 'MISSING_REGIME_RANGE' in r.rejection_reasons

def test_holm_bonferroni_tightens_alpha_for_multiple_trials():
    assert holm_bonferroni_alpha(.05,20)==pytest.approx(.0025)

def test_confidence_is_oos_calibrated_and_penalized_by_regime_features_and_data_quality():
    probs=[.1,.2,.2,.4,.6,.7,.8,.9]*10; outcomes=[0,0,0,0,1,1,1,1]*10
    c=ConfidenceCalibrator(probs,outcomes,oos_validated=True,buckets=5)
    strong=c.evidence(.8,regime_alignment=.95,feature_completeness=.95,data_quality=.95)
    weak=c.evidence(.8,regime_alignment=.5,feature_completeness=.6,data_quality=.7)
    assert strong.calibrated_probability>weak.calibrated_probability
    assert 0<=strong.brier_score<=1 and strong.similar_signal_count>0 and strong.bucket_observed_rate is not None
    with pytest.raises(ValueError): ConfidenceCalibrator(probs,outcomes,oos_validated=False)

def test_multi_asset_correlation_snapshot_tracks_exposure_beta_covariance_clusters_and_stress():
    x=np.linspace(-.02,.03,60); y=x*.9+np.sin(np.arange(60))*.001; z=-x*.2+np.cos(np.arange(60))*.003
    positions=[
      {'asset':'BTC','symbol':'BTCUSDT','quote':'USDT','exchange':'binance','market_type':'spot','strategy':'trend','notional':'400'},
      {'asset':'ETH','symbol':'ETHUSDT','quote':'USDT','exchange':'binance','market_type':'spot','strategy':'trend','notional':'300'},
      {'asset':'SOL','symbol':'SOLUSDT','quote':'USDT','exchange':'binance','market_type':'spot','strategy':'meanrev','notional':'-200'}]
    s=build_correlation_snapshot(positions=positions,returns={'BTCUSDT':x.tolist(),'ETHUSDT':y.tolist(),'SOLUSDT':z.tolist()},btc_returns=x.tolist(),eth_returns=y.tolist())
    assert s.exposure_by_quote['USDT']==Decimal('900') and s.directional_exposure['short']==Decimal('200')
    assert s.beta_to_btc['BTCUSDT']==pytest.approx(1,rel=1e-6) and s.correlated_cluster_exposure
    assert s.common_factor_exposure>0 and s.stress_cluster_exposure==Decimal('855.00')
    assert concentration_breaches(s,max_cluster=Decimal('500'),max_common_factor=Decimal('1000'),max_stress_cluster=Decimal('800'))

def test_signed_merkle_checkpoint_detects_record_or_chain_tampering_and_captures_required_audit_fields():
    hs=['00'*32,'11'*32,'22'*32]
    cp=create_checkpoint(hs,sequence=3,secret=b'super-secret',actor='admin',action='RISK_LIMIT_CHANGE',object_ref='risk/max_drawdown',correlation_id='corr-1',reason='approved change',release_version='0.3.0')
    assert verify_checkpoint(cp,hs,secret=b'super-secret',expected_previous_hash=None)
    assert not verify_checkpoint(cp,hs[:-1]+['33'*32],secret=b'super-secret',expected_previous_hash=None)
    assert {cp.actor,cp.action,cp.object_ref,cp.correlation_id,cp.reason,cp.release_version}
    cp2=create_checkpoint(['44'*32],sequence=4,secret=b'super-secret',previous_checkpoint_hash=cp.checkpoint_hash,actor='system',action='RECONCILE',object_ref='account',correlation_id='corr-2',reason='periodic',release_version='0.3.0')
    assert verify_checkpoint(cp2,['44'*32],secret=b'super-secret',expected_previous_hash=cp.checkpoint_hash)
    assert not verify_checkpoint(cp2,['44'*32],secret=b'super-secret',expected_previous_hash='bad')

def test_api_version_policy_enforces_backward_compatibility_window_deprecation_warning_and_breaking_change_definition():
    p=ApiVersionPolicy(compatibility_window_days=180,deprecation_warning_days=90); reg=ApiVersionRegistry(p)
    today=date(2026,1,1); notice=DeprecationNotice('v1',today,today+timedelta(days=120),'v2','authentication contract changes')
    reg.deprecate(notice); h=reg.headers('v1',today)
    assert h['Deprecation']=='true' and 'successor-version' in h['Link']
    assert reg.is_breaking_change(changes_auth=True) and not reg.is_breaking_change()
    with pytest.raises(ValueError): ApiVersionRegistry(ApiVersionPolicy(compatibility_window_days=30,deprecation_warning_days=90))
