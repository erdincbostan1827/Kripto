from datetime import datetime,timezone
from decimal import Decimal
import pytest
from app.audit.decision_evidence import DecisionEvidence,validate_decision_evidence

def evidence(**kw):
    base=dict(symbol='BTCUSDT',decision='BUY',reasons=('trend','volume'),indicators={'rsi':55.0,'ema50':100.0},parameters={'rsi_period':14,'risk_fraction':'0.0025'},market_price=Decimal('101.2'),data_timestamp=datetime.now(timezone.utc),risk={'stop':'98','risk_amount':'25'},order_reason='validated signal',exchange_response={'status':'ACKNOWLEDGED','order_id':'42'},portfolio_state={'correlation':0.2,'concentration':0.1},universe_snapshot_id='u1',metadata_version='m1',model_version='signal-v3',config_hash='abc')
    base.update(kw); return DecisionEvidence(**base)

def test_decision_evidence_captures_signal_indicators_parameters_price_time_risk_order_exchange_and_portfolio():
    e=validate_decision_evidence(evidence())
    c=e.canonical()
    assert c['reasons']==('trend','volume') and c['indicators']['rsi']==55.0
    assert c['parameters']['rsi_period']==14 and c['market_price']=='101.2'
    assert c['risk']['stop']=='98' and c['order_reason']=='validated signal'
    assert c['exchange_response']['status']=='ACKNOWLEDGED'
    assert c['portfolio_state']=={'correlation':0.2,'concentration':0.1}
    assert len(e.fingerprint())==64

def test_decision_evidence_fingerprint_is_reproducible_and_tamper_sensitive():
    t=datetime(2026,1,1,tzinfo=timezone.utc); a=evidence(data_timestamp=t); b=evidence(data_timestamp=t)
    assert a.fingerprint()==b.fingerprint()
    assert a.fingerprint()!=evidence(data_timestamp=t,market_price=Decimal('101.3')).fingerprint()

def test_order_decision_without_exchange_response_fails_closed():
    with pytest.raises(ValueError,match='exchange response'): validate_decision_evidence(evidence(exchange_response=None))
