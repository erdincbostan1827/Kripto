import pytest
from app.execution.emergency import EmergencyController
from app.risk.state import RiskMachine
from app.core.enums import RiskState

def test_emergency_stop_preserves_protection_and_does_not_panic_close():
    r=RiskMachine(); x=EmergencyController(r).emergency_stop(); assert r.state==RiskState.HALTED and x.preserve_protective_orders and not x.close_positions

def test_panic_close_is_separate_human_approved_action():
    c=EmergencyController(RiskMachine())
    with pytest.raises(PermissionError): c.panic_close(False)
    assert c.panic_close(True).close_positions
