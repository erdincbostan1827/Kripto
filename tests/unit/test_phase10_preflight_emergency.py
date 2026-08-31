from app.core.enums import RiskState
from app.execution.emergency import EmergencyController, EmergencyPolicy
from app.monitoring.health import HealthService, ProbeResult
from app.monitoring.selftest import SelfTestService
from app.risk.state import RiskMachine


def test_health_snapshot_is_fail_closed_for_all_operational_components():
    ok=lambda: ProbeResult('UP',0.1)
    probes={k:ok for k in HealthService.OPERATIONAL_COMPONENTS}
    snap=HealthService(probes,fail_closed=True,required_components=HealthService.OPERATIONAL_COMPONENTS).snapshot()
    assert snap['ready_for_new_risk'] is True
    probes.pop('websocket')
    snap=HealthService(probes,fail_closed=True,required_components=HealthService.OPERATIONAL_COMPONENTS).snapshot()
    assert snap['ready_for_new_risk'] is False and snap['websocket']=='UNCONFIGURED'


def test_selftest_never_promotes_unconfigured_external_dependency_to_pass(tmp_path):
    ok=lambda: ProbeResult('UP',0.1)
    health=HealthService({k:ok for k in ('database','redis','exchange','clock')},fail_closed=True)
    result=SelfTestService(health,disk_path=str(tmp_path),min_free_disk_bytes=1).run()
    assert result['status']=='FAIL'
    assert 'api_credentials' in result['failures'] and 'websocket' in result['failures']


def test_selftest_passes_only_when_all_required_checks_are_explicitly_green(tmp_path):
    ok=lambda: ProbeResult('UP',0.1)
    health=HealthService({k:ok for k in ('database','redis','exchange','clock')},fail_closed=True)
    yes=lambda: True
    result=SelfTestService(
        health, environment_check=yes, credential_check=yes, permission_check=yes, telegram_check=yes,
        websocket_check=yes, risk_config_check=yes, strategy_config_check=yes,
        docker_check=yes, memory_check=yes, disk_path=str(tmp_path), min_free_disk_bytes=1,
    ).run()
    assert result['status']=='PASS' and result['ready_for_new_risk'] is True and not result['failures']


def test_emergency_stop_policy_preserves_protective_orders_and_configures_position_close():
    risk=RiskMachine()
    policy=EmergencyPolicy(close_positions_on_stop=True)
    result=EmergencyController(risk,policy).emergency_stop('LOSS_LIMIT')
    assert risk.state==RiskState.HALTED and risk.allow_new_risk() is False
    assert result.cancel_unprotected_entry_orders is True
    assert result.preserve_protective_orders is True
    assert result.close_positions is True
