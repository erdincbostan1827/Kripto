from decimal import Decimal

from app.core.enums import RiskState
from app.execution.reconciliation import AccountSnapshot
from app.execution.recovery import RestartRecoveryCoordinator
from app.risk.state import RecoveryChecks


def green_checks():
    return RecoveryChecks(
        data_healthy=True,
        exchange_healthy=True,
        private_stream_healthy=True,
        reconciliation_ok=True,
        no_orphan_orders=True,
        protective_orders_ok=True,
        risk_limits_ok=True,
        clock_ok=True,
        strategy_health_ok=True,
    )


def snapshot(balance="1000", position="0", orders=()):
    positions = {} if position == "0" else {"BTCUSDT": Decimal(position)}
    return AccountSnapshot({"USDT": Decimal(balance)}, positions, set(orders))


def test_restart_recovery_blocks_new_risk_until_reconciliation_human_approval_and_green_gates():
    coordinator = RestartRecoveryCoordinator()
    coordinator.begin()
    assert coordinator.risk.state == RiskState.RECOVERY_PENDING
    assert not coordinator.risk.allow_new_risk()

    evidence = coordinator.evaluate(
        local=snapshot(), exchange=snapshot(), checks=green_checks(), human_approved=False
    )
    assert not evidence.ready_for_active
    assert coordinator.risk.state == RiskState.RECOVERY_PENDING
    assert not coordinator.risk.allow_new_risk()

    evidence = coordinator.evaluate(
        local=snapshot(), exchange=snapshot(), checks=green_checks(), human_approved=True
    )
    assert evidence.ready_for_active
    assert coordinator.risk.state == RiskState.ACTIVE
    assert coordinator.risk.allow_new_risk()


def test_restart_recovery_detects_external_drift_and_requires_manual_review():
    coordinator = RestartRecoveryCoordinator()
    coordinator.begin()
    evidence = coordinator.evaluate(
        local=snapshot(balance="1000"),
        exchange=snapshot(balance="999", orders=("orphan-1",)),
        checks=green_checks(),
        human_approved=True,
    )
    assert evidence.reconciliation.drift
    assert not evidence.ready_for_active
    assert coordinator.risk.state == RiskState.MANUAL_REVIEW_REQUIRED
    assert not coordinator.risk.allow_new_risk()


def test_committed_account_state_survives_abrupt_worker_exit(tmp_path):
    import os
    import subprocess
    import sys
    from pathlib import Path

    from app.database.session import make_engine
    from app.execution.local_snapshot import DatabaseAccountSnapshotProvider
    from app.database.session import session_factory

    db_path = tmp_path / "restart.db"
    project_root = Path(__file__).resolve().parents[2]
    code = r'''
import os, sys
from decimal import Decimal
from app.database.session import make_engine, init_db, session_factory
from app.database.models import ExchangeAccount, AccountBalance
url=sys.argv[1]
e=make_engine(url)
init_db(e)
sf=session_factory(e)
with sf() as s:
    s.add(ExchangeAccount(id='acct', exchange='BINANCE', account_fingerprint='fp', market_type='SPOT', capabilities={}, permission_snapshot={}, status='ACTIVE'))
    s.add(AccountBalance(id='bal', exchange_account_id='acct', asset='USDT', free=Decimal('1234.5'), locked=Decimal('0'),))
    s.commit()
os._exit(137)
'''
    env = dict(os.environ)
    env["PYTHONPATH"] = str(project_root / "backend") + os.pathsep + env.get("PYTHONPATH", "")
    proc = subprocess.run(
        [sys.executable, "-c", code, f"sqlite+pysqlite:///{db_path}"],
        cwd=project_root,
        env=env,
        check=False,
    )
    assert proc.returncode != 0

    engine = make_engine(f"sqlite+pysqlite:///{db_path}")
    snap = DatabaseAccountSnapshotProvider(session_factory(engine)).snapshot("acct")
    assert snap.balances["USDT"] == Decimal("1234.5")
    engine.dispose()


def test_partial_fill_is_reconstructed_from_committed_fills_after_restart(tmp_path):
    from app.database.session import make_engine, init_db, session_factory
    from app.database.models import ExchangeAccount, Order, Fill
    from app.execution.recovery import recover_durable_order

    db_path = tmp_path / 'partial-fill.db'
    engine = make_engine(f'sqlite+pysqlite:///{db_path}')
    init_db(engine)
    sf = session_factory(engine)
    with sf() as s:
        s.add(ExchangeAccount(id='acct', exchange='BINANCE', account_fingerprint='fp', market_type='SPOT', capabilities={}, permission_snapshot={}, status='ACTIVE'))
        s.add(Order(id='order1', intent_id='intent1', exchange_account_id='acct', symbol='BTCUSDT', side='BUY', order_type='LIMIT', quantity=Decimal('1'), price=Decimal('60000'), status='PARTIALLY_FILLED', exchange_order_id='ex1', client_order_id='ctp-intent1'))
        s.add(Fill(id='fill1', exchange_account_id='acct', order_id='order1', trade_id='trade1', quantity=Decimal('0.4'), price=Decimal('60000'), fee_asset='USDT', fee_amount=Decimal('1')))
        s.commit()

    recovered = recover_durable_order(sf, 'intent1')
    assert recovered.status == 'PARTIALLY_FILLED'
    assert abs(Decimal(recovered.filled_quantity) - Decimal('0.4')) < Decimal('1e-15')
    assert abs(Decimal(recovered.remaining_quantity) - Decimal('0.6')) < Decimal('1e-15')
    assert recovered.consistent
    engine.dispose()


def test_restart_detects_contradictory_filled_status_and_partial_durable_fill(tmp_path):
    from app.database.session import make_engine, init_db, session_factory
    from app.database.models import ExchangeAccount, Order, Fill
    from app.execution.recovery import recover_durable_order

    db_path = tmp_path / 'contradictory-fill.db'
    engine = make_engine(f'sqlite+pysqlite:///{db_path}')
    init_db(engine)
    sf = session_factory(engine)
    with sf() as s:
        s.add(ExchangeAccount(id='acct', exchange='BINANCE', account_fingerprint='fp', market_type='SPOT', capabilities={}, permission_snapshot={}, status='ACTIVE'))
        s.add(Order(id='order1', intent_id='intent1', exchange_account_id='acct', symbol='BTCUSDT', side='BUY', order_type='LIMIT', quantity=Decimal('1'), price=Decimal('60000'), status='FILLED', exchange_order_id='ex1', client_order_id='ctp-intent1'))
        s.add(Fill(id='fill1', exchange_account_id='acct', order_id='order1', trade_id='trade1', quantity=Decimal('0.4'), price=Decimal('60000'), fee_asset='USDT', fee_amount=Decimal('1')))
        s.commit()

    recovered = recover_durable_order(sf, 'intent1')
    assert not recovered.consistent
    assert abs(Decimal(recovered.remaining_quantity) - Decimal('0.6')) < Decimal('1e-15')
    engine.dispose()
