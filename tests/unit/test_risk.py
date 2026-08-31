from decimal import Decimal
import pytest
from app.risk.engine import *
from app.risk.state import RiskMachine
from app.risk.circuit import CircuitBreaker
from app.risk.portfolio import cluster_exposure
from app.core.enums import RiskState

def test_position_sizing_positive(): assert size_position('10000','100','95','0.001','0.01')>0
def test_position_size_reduces_with_wider_stop(): assert size_position('10000','100','90','0.001','0.01')<size_position('10000','100','95','0.001','0.01')
def test_costs_in_effective_loss(): assert effective_loss_per_unit('100','95')>Decimal('5')
def test_daily_loss_blocks(): assert 'DAILY_LOSS' in validate_portfolio(RiskSnapshot(Decimal('10000'),daily_pnl=Decimal('-300')),RiskLimits())
def test_weekly_loss_blocks(): assert 'WEEKLY_LOSS' in validate_portfolio(RiskSnapshot(Decimal('10000'),weekly_pnl=Decimal('-600')),RiskLimits())
def test_drawdown_blocks(): assert 'MAX_DRAWDOWN' in validate_portfolio(RiskSnapshot(Decimal('10000'),drawdown=Decimal('.11')),RiskLimits())
def test_exposure_blocks(): assert 'PORTFOLIO_EXPOSURE' in validate_portfolio(RiskSnapshot(Decimal('10000'),gross_exposure=Decimal('6000')),RiskLimits())
def test_asset_exposure_blocks(): assert 'SINGLE_ASSET_EXPOSURE' in validate_portfolio(RiskSnapshot(Decimal('10000'),asset_exposure=Decimal('2000')),RiskLimits())
def test_position_count_blocks(): assert 'MAX_POSITIONS' in validate_portfolio(RiskSnapshot(Decimal('10000'),open_positions=6),RiskLimits())
def test_risk_machine_recovery_needs_human():
 r=RiskMachine(); r.halt('x')
 with pytest.raises(PermissionError): r.recover(False,True)
def test_risk_machine_recovery():
 r=RiskMachine(); r.halt('x'); r.recover(True,True); assert r.state==RiskState.NORMAL
def test_circuit_fatal_halts(): assert CircuitBreaker().evaluate(database_ok=False,exchange_ok=True)==RiskState.HALTED
def test_circuit_nonfatal_restricts(): assert CircuitBreaker().evaluate(telegram_ok=False)==RiskState.RESTRICTED
def test_cluster_exposure():
 groups=cluster_exposure({'BTC':Decimal('10'),'ETH':Decimal('5'),'DOGE':Decimal('2')},{('BTC','ETH'):.9}); assert any(g=={'BTC','ETH'} and x==Decimal('15') for g,x in groups)

def test_quote_asset_exposure_blocks():
 assert 'QUOTE_ASSET_EXPOSURE' in validate_portfolio(RiskSnapshot(Decimal('10000'),quote_asset_exposure=Decimal('9000')),RiskLimits())

def test_volatility_adjusted_exposure_blocks():
 assert 'VOLATILITY_ADJUSTED_EXPOSURE' in validate_portfolio(RiskSnapshot(Decimal('10000'),volatility_adjusted_exposure=Decimal('7000')),RiskLimits())

def test_consecutive_losses_block():
 assert 'CONSECUTIVE_LOSSES' in validate_portfolio(RiskSnapshot(Decimal('10000'),consecutive_losses=5),RiskLimits())

def test_funding_borrow_cost_increases_effective_loss_when_applicable():
 base=effective_loss_per_unit('100','95',funding_borrow_bps=0)
 stressed=effective_loss_per_unit('100','95',funding_borrow_bps=25)
 assert stressed>base


def test_formal_risk_states_are_explicit():
    required = {"STARTING", "PAPER_ONLY", "ACTIVE", "DEGRADED", "REDUCING_ONLY", "HALTED", "RECOVERY_PENDING", "MANUAL_REVIEW_REQUIRED", "STOPPING"}
    assert required <= {state.value for state in RiskState}


def test_halted_recovery_requires_human_and_all_green_checks():
    from app.risk.state import RecoveryChecks

    r = RiskMachine()
    r.halt("exchange_disconnect")
    with pytest.raises(PermissionError):
        r.recover(False, checks=RecoveryChecks(**{name: True for name in RecoveryChecks.__dataclass_fields__}))
    assert r.state == RiskState.RECOVERY_PENDING

    r.halt("retry")
    incomplete = RecoveryChecks(data_healthy=True, exchange_healthy=True)
    with pytest.raises(PermissionError):
        r.recover(True, checks=incomplete)
    assert r.state == RiskState.RECOVERY_PENDING


def test_recovery_pending_can_promote_to_active_only_after_all_gates():
    from app.risk.state import RecoveryChecks

    r = RiskMachine()
    r.halt("fault")
    r.recovery_pending()
    checks = RecoveryChecks(**{name: True for name in RecoveryChecks.__dataclass_fields__})
    r.recover(True, checks=checks, target=RiskState.ACTIVE)
    assert r.state == RiskState.ACTIVE
    assert r.allow_new_risk()


def test_halted_cannot_jump_directly_to_active_even_with_green_checks():
    from app.risk.state import RecoveryChecks

    r = RiskMachine()
    r.halt("fault")
    checks = RecoveryChecks(**{name: True for name in RecoveryChecks.__dataclass_fields__})
    with pytest.raises(PermissionError):
        r.recover(True, checks=checks, target=RiskState.ACTIVE)
    assert r.state == RiskState.HALTED


def test_risk_state_allowed_actions_are_fail_closed():
    r = RiskMachine()
    r.halt("fault")
    assert "OPEN" not in r.allowed_actions()
    assert {"CANCEL", "CLOSE", "RECOVER"} <= r.allowed_actions()
    r.reducing_only("risk_limit")
    assert "OPEN" not in r.allowed_actions()
    assert "REDUCE" in r.allowed_actions()
