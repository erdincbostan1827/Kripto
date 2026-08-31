import pytest
from app.core.live_gate import *
from app.core.enums import TradingMode

def evidence(value=True): return LiveGateEvidence('r1',{k:value for k in MANDATORY_GATES})
def test_paper_no_gate_needed(): require_live_gate(TradingMode.PAPER,None,False)
def test_live_full_gate(): require_live_gate(TradingMode.LIVE,evidence(),True)
def test_live_incomplete_blocked():
    e=evidence(); e.gates['TESTNET']=False
    with pytest.raises(PermissionError): require_live_gate(TradingMode.LIVE,e,True)
def test_live_confirmation_blocked():
    with pytest.raises(PermissionError): require_live_gate(TradingMode.LIVE,evidence(),False)
def test_blocker_list():
    e=evidence(); e.gates['OOS']=False; assert e.blockers()==['OOS']
