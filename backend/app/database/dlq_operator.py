from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Callable

from .models import DeadLetterRow, OutboxEvent


def payload_hash(payload: dict) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return sha256(raw).hexdigest()


@dataclass(frozen=True)
class DeadLetterInspection:
    original_event_id: str
    event_type: str
    schema_version: int
    payload_hash: str
    failure_reason: str
    attempts: int
    resolution_state: str
    payload: dict


class DeadLetterOperator:
    def __init__(self, session_factory):
        self.sf = session_factory

    def inspect(self, original_event_id: str) -> DeadLetterInspection:
        with self.sf() as s:
            dlq = s.query(DeadLetterRow).filter_by(original_event_id=original_event_id).one_or_none()
            outbox = s.query(OutboxEvent).filter_by(event_id=original_event_id).one_or_none()
            if dlq is None or outbox is None:
                raise LookupError(original_event_id)
            actual = payload_hash(outbox.payload)
            if dlq.payload_hash and dlq.payload_hash != actual:
                raise RuntimeError("DEAD_LETTER_PAYLOAD_HASH_MISMATCH")
            return DeadLetterInspection(
                dlq.original_event_id, dlq.event_type, dlq.schema_version, actual,
                dlq.failure_reason, dlq.attempts, dlq.resolution_state, dict(outbox.payload),
            )

    def migrate_payload(self, original_event_id: str, *, expected_hash: str, new_schema_version: int, migrator: Callable[[dict], dict]) -> DeadLetterInspection:
        with self.sf() as s:
            dlq = s.query(DeadLetterRow).filter_by(original_event_id=original_event_id).one_or_none()
            outbox = s.query(OutboxEvent).filter_by(event_id=original_event_id).one_or_none()
            if dlq is None or outbox is None:
                raise LookupError(original_event_id)
            if dlq.resolution_state not in {"OPEN", "MIGRATED"}:
                raise RuntimeError("DEAD_LETTER_NOT_MIGRATABLE")
            current = payload_hash(outbox.payload)
            if current != expected_hash:
                raise RuntimeError("DEAD_LETTER_STALE_OPERATOR_VIEW")
            migrated = dict(migrator(dict(outbox.payload)))
            outbox.payload = migrated
            dlq.schema_version = int(new_schema_version)
            dlq.payload_hash = payload_hash(migrated)
            dlq.resolution_state = "MIGRATED"
            s.commit()
        return self.inspect(original_event_id)

    def schedule_replay(self, original_event_id: str, *, expected_hash: str) -> None:
        with self.sf() as s:
            dlq = s.query(DeadLetterRow).filter_by(original_event_id=original_event_id).one_or_none()
            outbox = s.query(OutboxEvent).filter_by(event_id=original_event_id).one_or_none()
            if dlq is None or outbox is None:
                raise LookupError(original_event_id)
            if payload_hash(outbox.payload) != expected_hash or dlq.payload_hash != expected_hash:
                raise RuntimeError("DEAD_LETTER_REPLAY_HASH_MISMATCH")
            if dlq.resolution_state not in {"OPEN", "MIGRATED"}:
                raise RuntimeError("DEAD_LETTER_NOT_REPLAYABLE")
            outbox.published_at = None
            outbox.attempts = 0
            outbox.next_attempt_at = None
            outbox.last_error = None
            dlq.resolution_state = "REPLAY_PENDING"
            s.commit()

    def mark_resolved(self, original_event_id: str) -> None:
        with self.sf() as s:
            dlq = s.query(DeadLetterRow).filter_by(original_event_id=original_event_id).one_or_none()
            outbox = s.query(OutboxEvent).filter_by(event_id=original_event_id).one_or_none()
            if dlq is None or outbox is None:
                raise LookupError(original_event_id)
            if dlq.resolution_state != "REPLAY_PENDING" or outbox.published_at is None:
                raise RuntimeError("DEAD_LETTER_REPLAY_NOT_CONFIRMED")
            dlq.resolution_state = "RESOLVED"
            s.commit()
