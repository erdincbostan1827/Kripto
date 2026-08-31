from app.core.lifecycle import GracefulShutdown
from app.core.enums import RiskState

class Risk: state=RiskState.ACTIVE

def test_graceful_shutdown_orders_entry_scheduler_reconcile_snapshot_db_outbox_and_stopping():
    calls=[]; r=Risk()
    g=GracefulShutdown(r,lambda:calls.append('scheduler'),lambda:calls.append('reconcile'),lambda:(calls.append('snapshot') or {'positions':1}),lambda:calls.append('db'),lambda:calls.append('outbox'))
    report=g.run()
    assert r.state==RiskState.STOPPING
    assert calls==['scheduler','reconcile','snapshot','db','outbox']
    assert report.clean and report.outbox_flushed and report.snapshot=={'positions':1}
    assert report.steps[0]=='NEW_ENTRIES_STOP' and report.steps[-1]=='CLEAN_SHUTDOWN'

def test_graceful_shutdown_outbox_is_best_effort_but_never_skips_db_flush():
    calls=[]; r=Risk()
    def bad(): calls.append('outbox'); raise RuntimeError('broker down')
    report=GracefulShutdown(r,lambda:calls.append('scheduler'),lambda:calls.append('reconcile'),lambda:{},lambda:calls.append('db'),bad).run()
    assert calls[-2:]==['db','outbox'] and report.clean and not report.outbox_flushed
    assert 'OUTBOX_FLUSH_FAILED_BEST_EFFORT' in report.steps
