import pytest
from app.strategies.lifecycle import StrategyLifecycle,StrategyVersionManifest

def test_strategy_promotion_is_sequential_and_provenance_manifest_is_complete():
    m=StrategyVersionManifest('s1','cfg','gitsha','dataset-v2','ind-v3','conservative-intrabar-v1','risk-v4').validate()
    assert m.strategy_version=='s1' and m.execution_model_version=='conservative-intrabar-v1'
    s=StrategyLifecycle('alpha')
    assert s.promote('BACKTEST_VALIDATED',{'backtest':True})=='BACKTEST_VALIDATED'
    assert s.promote('OOS_VALIDATED',{'oos':True})=='OOS_VALIDATED'
    with pytest.raises(PermissionError): s.promote('TESTNET_VALIDATED',{'testnet':True})

def test_strategy_provenance_rejects_missing_version_dimension():
    with pytest.raises(ValueError): StrategyVersionManifest('s1','cfg','','d','i','e','r').validate()
