from __future__ import annotations

import hashlib
from decimal import Decimal
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.audit.storage import AuditStoragePolicy
from app.data.orderbook import LocalOrderBook, OrderBookIntegrityError
from app.database.models import Base
from app.release.fault_contract import FaultKind, evaluate_external_fault
from app.release.provenance import ReleaseAttestation
from app.risk.portfolio_optimizer import OptimizerPolicy, constrained_edge_optimizer
from app.services.setup_wizard import SetupWizardService

ROOT = Path(__file__).resolve().parents[2]


def test_phase23_orderbook_checksum_is_conditional_and_mismatch_invalidates_book():
    book=LocalOrderBook(); book.load_snapshot(10, [('100','2'),('99','3')], [('101','4'),('102','5')])
    assert book.verify_exchange_checksum(None) is True and book.checksum_verified is None
    expected=hashlib.sha256(book.canonical_checksum_payload()).hexdigest()
    assert book.verify_exchange_checksum(expected) and book.valid and book.checksum_verified is True
    with pytest.raises(OrderBookIntegrityError, match='checksum mismatch'):
        book.verify_exchange_checksum('0'*64)
    assert not book.valid and book.checksum_verified is False


def test_phase23_optimizer_default_is_constrained_not_unbounded_mean_variance():
    policy=OptimizerPolicy().validate()
    result=constrained_edge_optimizer({'BTCUSDT':Decimal('30'),'ETHUSDT':Decimal('20'),'MEMEUSDT':Decimal('-5')}, policy=policy)
    assert result.gross_weight <= policy.max_gross_weight
    assert result.cash_weight >= Decimal('0.15')
    assert all(w <= policy.max_single_asset_weight for w in result.weights.values())
    assert 'MEMEUSDT:NON_POSITIVE_EDGE' in result.blocked
    with pytest.raises(ValueError): OptimizerPolicy(max_single_asset_weight=Decimal('1.1')).validate()


def test_phase23_rest_timeout_and_dns_failure_are_fail_closed_fault_contracts():
    rest=evaluate_external_fault(FaultKind.REST_TIMEOUT)
    dns=evaluate_external_fault(FaultKind.DNS_FAILURE)
    assert not rest.allow_new_risk and rest.require_reconciliation and rest.health=='DEGRADED'
    assert not dns.allow_new_risk and dns.require_reconciliation and dns.health=='DOWN'


def test_phase23_setup_preferences_validate_iana_timezone_and_notification_booleans(tmp_path):
    engine=create_engine(f"sqlite:///{tmp_path/'wizard.db'}")
    Base.metadata.create_all(engine)
    sf=sessionmaker(engine, expire_on_commit=False)
    svc=SetupWizardService(sf); svc.start_or_resume()
    for step in range(1,7): svc.complete_step('default', step, {})
    snap=svc.complete_step('default',7,{'timezone':'Europe/Istanbul','notifications':{'telegram':True,'email':False,'critical_only':True}})
    prefs=snap.non_secret_config['step_7']
    assert prefs['timezone']=='Europe/Istanbul' and prefs['notifications']['telegram'] is True
    engine.dispose()
    engine2=create_engine(f"sqlite:///{tmp_path/'bad.db'}"); Base.metadata.create_all(engine2)
    svc2=SetupWizardService(sessionmaker(engine2, expire_on_commit=False)); svc2.start_or_resume()
    for step in range(1,7): svc2.complete_step('default',step,{})
    with pytest.raises(ValueError, match='IANA timezone'): svc2.complete_step('default',7,{'timezone':'Mars/Olympus'})
    engine2.dispose()


def test_phase23_release_identity_requires_real_provenance_for_production_and_manifest_has_timestamp():
    import json
    manifest=json.loads((ROOT/'RELEASE_MANIFEST.json').read_text())
    assert manifest['release_id']=='0.3.0-local-acceptance'
    assert manifest['build_timestamp'] and 'T' in manifest['build_timestamp']
    att=ReleaseAttestation(
        release_id='0.3.0-local-acceptance', git_commit_sha='UNAVAILABLE', source_tree_hash='a'*64,
        ci_run_id='LOCAL-NOT-CI', build_timestamp=manifest['build_timestamp'], dependency_lock_hash=None,
        sbom_hash=None, container_digest='NOT_BUILT', frontend_artifact_hash=None, migration_version='0003',
        architecture_profile_hash='b'*64, requirement_matrix_hash='c'*64, test_evidence_reference='reports/LATEST_PYTEST.txt')
    blockers=set(att.production_blockers())
    assert {'git_commit_sha','ci_run_id','dependency_lock_hash','sbom_hash','container_digest','frontend_artifact_hash'} <= blockers
    with pytest.raises(ValueError, match='incomplete release provenance'): att.assert_production_complete()


def test_phase23_worm_storage_policy_rejects_mutable_or_non_worm_production_sink():
    class Sink:
        def __init__(self, append_only, worm_capable): self.append_only=append_only; self.worm_capable=worm_capable
        def append(self,payload): return hashlib.sha256(payload).hexdigest()
    policy=AuditStoragePolicy()
    with pytest.raises(ValueError, match='append-only'): policy.validate_sink(Sink(False,True), production=False)
    policy.validate_sink(Sink(True,False), production=False)
    with pytest.raises(ValueError, match='WORM-capable'): policy.validate_sink(Sink(True,False), production=True)
    policy.validate_sink(Sink(True,True), production=True)


def test_phase23_rejected_order_is_terminal_and_not_retried_as_duplicate():
    from app.exchange.mock import MockExchange
    from app.exchange.models import OrderIntent
    from app.execution.service import ExecutionService
    from app.risk.state import RiskMachine
    from app.core.enums import OrderState
    exchange=MockExchange(); exchange.fail_mode='reject'
    service=ExecutionService(exchange,RiskMachine())
    intent=OrderIntent('reject-1','a1','BTCUSDT','BUY','LIMIT',Decimal('0.01'),Decimal('60000'))
    first=service.submit(intent,Decimal('60000'),Decimal('100'))
    second=service.submit(intent,Decimal('60000'),Decimal('100'))
    assert first.state is OrderState.REJECTED and second.state is OrderState.REJECTED
    assert len(exchange.orders)==1


def test_phase23_local_secret_scanner_executes_and_reports_zero_findings():
    import subprocess,sys
    run=subprocess.run([sys.executable,'scripts/secret_scan.py'],cwd=ROOT,text=True,capture_output=True,check=False)
    assert run.returncode==0, run.stdout+run.stderr
    assert 'PASS files_scanned=' in run.stdout and 'findings=0' in run.stdout
