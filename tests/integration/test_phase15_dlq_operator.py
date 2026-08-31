from datetime import datetime, timezone
import uuid

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.models import Base
from app.database.dlq_operator import DeadLetterOperator
from app.database.models import DeadLetterRow, OutboxEvent
from app.database.outbox import OutboxDispatcher


def _sf():
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, expire_on_commit=False)


def test_dlq_operator_inspect_migrate_safe_replay_and_resolve_flow():
    sf = _sf()
    event_id = uuid.uuid4().hex
    with sf() as s:
        s.add(OutboxEvent(id=uuid.uuid4().hex, event_id=event_id, topic="ORDER_EVENT", payload={"schema_version": 1, "qty": "1"}))
        s.commit()
    failing = OutboxDispatcher(sf, lambda *_: (_ for _ in ()).throw(RuntimeError("poison")), max_attempts=1)
    assert failing.dispatch_once(now=datetime.now(timezone.utc))["failed"] == 1

    operator = DeadLetterOperator(sf)
    initial = operator.inspect(event_id)
    assert initial.resolution_state == "OPEN" and len(initial.payload_hash) == 64
    migrated = operator.migrate_payload(
        event_id, expected_hash=initial.payload_hash, new_schema_version=2,
        migrator=lambda p: {"schema_version": 2, "quantity": p["qty"]},
    )
    assert migrated.resolution_state == "MIGRATED" and migrated.payload["quantity"] == "1"
    operator.schedule_replay(event_id, expected_hash=migrated.payload_hash)

    delivered = []
    dispatcher = OutboxDispatcher(sf, lambda topic, payload: delivered.append((topic, payload)), max_attempts=2)
    assert dispatcher.dispatch_once(now=datetime.now(timezone.utc))["published"] == 1
    operator.mark_resolved(event_id)
    assert operator.inspect(event_id).resolution_state == "RESOLVED"
    assert delivered[0][1] == {"schema_version": 2, "quantity": "1"}
    sf.kw["bind"].dispose()


def test_dlq_operator_rejects_stale_operator_hash_and_unconfirmed_resolution():
    sf = _sf()
    event_id = uuid.uuid4().hex
    with sf() as s:
        s.add(OutboxEvent(id=uuid.uuid4().hex, event_id=event_id, topic="X", payload={"v": 1}))
        s.commit()
    OutboxDispatcher(sf, lambda *_: (_ for _ in ()).throw(RuntimeError("bad")), max_attempts=1).dispatch_once(now=datetime.now(timezone.utc))
    operator = DeadLetterOperator(sf)
    with pytest.raises(RuntimeError, match="STALE_OPERATOR_VIEW"):
        operator.migrate_payload(event_id, expected_hash="0" * 64, new_schema_version=2, migrator=lambda p: p)
    current = operator.inspect(event_id)
    operator.schedule_replay(event_id, expected_hash=current.payload_hash)
    with pytest.raises(RuntimeError, match="REPLAY_NOT_CONFIRMED"):
        operator.mark_resolved(event_id)
    sf.kw["bind"].dispose()
