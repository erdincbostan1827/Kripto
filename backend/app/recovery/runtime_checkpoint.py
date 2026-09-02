from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import hmac
import json
from typing import Any


def _canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


@dataclass(frozen=True)
class RuntimeCheckpoint:
    version: int
    created_at_unix: float
    risk_state: str
    config_hash: str
    last_event_sequence: int
    positions: dict[str, str]
    open_order_ids: tuple[str, ...]
    reservations: dict[str, str]
    event_chain_hash: str
    payload_hash: str
    signature: str

    def unsigned_payload(self) -> dict[str, Any]:
        data = asdict(self)
        data.pop("payload_hash")
        data.pop("signature")
        return data


@dataclass(frozen=True)
class RestoreDecision:
    allowed: bool
    reasons: tuple[str, ...]
    checkpoint_age_seconds: float


def create_runtime_checkpoint(
    *,
    secret: bytes,
    created_at_unix: float,
    risk_state: str,
    config_hash: str,
    last_event_sequence: int,
    positions: dict[str, str],
    open_order_ids: list[str] | tuple[str, ...],
    reservations: dict[str, str],
    event_chain_hash: str,
    version: int = 1,
) -> RuntimeCheckpoint:
    if not secret:
        raise ValueError("checkpoint signing secret is required")
    if last_event_sequence < 0:
        raise ValueError("last_event_sequence must be non-negative")
    normalized_created_at = float(created_at_unix)
    normalized_risk_state = str(risk_state)
    normalized_config_hash = str(config_hash)
    normalized_sequence = int(last_event_sequence)
    normalized_positions = {str(k): str(v) for k, v in sorted(positions.items())}
    normalized_order_ids = tuple(sorted(str(x) for x in open_order_ids))
    normalized_reservations = {str(k): str(v) for k, v in sorted(reservations.items())}
    normalized_event_chain_hash = str(event_chain_hash)
    unsigned = {
        "version": version,
        "created_at_unix": normalized_created_at,
        "risk_state": normalized_risk_state,
        "config_hash": normalized_config_hash,
        "last_event_sequence": normalized_sequence,
        "positions": normalized_positions,
        "open_order_ids": normalized_order_ids,
        "reservations": normalized_reservations,
        "event_chain_hash": normalized_event_chain_hash,
    }
    payload_hash = sha256(_canonical(unsigned)).hexdigest()
    signature = hmac.new(secret, payload_hash.encode("ascii"), sha256).hexdigest()
    return RuntimeCheckpoint(
        version=version,
        created_at_unix=normalized_created_at,
        risk_state=normalized_risk_state,
        config_hash=normalized_config_hash,
        last_event_sequence=normalized_sequence,
        positions=normalized_positions,
        open_order_ids=normalized_order_ids,
        reservations=normalized_reservations,
        event_chain_hash=normalized_event_chain_hash,
        payload_hash=payload_hash,
        signature=signature,
    )


def verify_runtime_checkpoint(checkpoint: RuntimeCheckpoint, *, secret: bytes) -> bool:
    unsigned = checkpoint.unsigned_payload()
    expected_hash = sha256(_canonical(unsigned)).hexdigest()
    if not hmac.compare_digest(expected_hash, checkpoint.payload_hash):
        return False
    expected_signature = hmac.new(secret, expected_hash.encode("ascii"), sha256).hexdigest()
    return hmac.compare_digest(expected_signature, checkpoint.signature)


def evaluate_restore(
    checkpoint: RuntimeCheckpoint,
    *,
    secret: bytes,
    now_unix: float,
    current_config_hash: str,
    current_event_sequence: int,
    current_event_chain_hash: str,
    max_checkpoint_age_seconds: float,
) -> RestoreDecision:
    reasons: list[str] = []
    age = float(now_unix) - checkpoint.created_at_unix
    if age < 0:
        reasons.append("CHECKPOINT_FROM_FUTURE")
    if age > max_checkpoint_age_seconds:
        reasons.append("CHECKPOINT_STALE")
    if not verify_runtime_checkpoint(checkpoint, secret=secret):
        reasons.append("CHECKPOINT_SIGNATURE_INVALID")
    if checkpoint.config_hash != current_config_hash:
        reasons.append("CONFIG_HASH_MISMATCH")
    if checkpoint.last_event_sequence != current_event_sequence:
        reasons.append("EVENT_SEQUENCE_MISMATCH")
    if checkpoint.event_chain_hash != current_event_chain_hash:
        reasons.append("EVENT_CHAIN_HASH_MISMATCH")
    return RestoreDecision(not reasons, tuple(reasons), age)
