from __future__ import annotations

import hashlib
import hmac
import json
import os
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

from app.paper.engine import PaperFill, PaperPosition
from app.release.campaign_collector import telemetry_key_id
from app.release.campaign_runtime_adapter import ProtectedCampaignRuntimeAdapter

SCHEMA_VERSION = "1.0"
CLASSIFICATION = "PHASE266_PROTECTED_CAMPAIGN_RUNTIME_STATE"
ATTESTATION_SCHEME = "HMAC-SHA256"


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(value: datetime) -> str:
    if value.tzinfo is None:
        raise ValueError("runtime-state timestamps must be timezone-aware")
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _canonical(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _key_bytes(value: str) -> bytes:
    raw = value.encode("utf-8")
    if len(raw) < 32:
        raise ValueError("Phase266 runtime-state HMAC key must contain at least 32 UTF-8 bytes")
    return raw


def _exact_hex(value: str, length: int, *, field: str) -> str:
    normalized = value.strip().lower()
    if len(normalized) != length or any(ch not in "0123456789abcdef" for ch in normalized):
        raise ValueError(f"{field} must be exact {length}-character lowercase hex")
    return normalized


def runtime_state_path(state_dir: Path, *, repository_root: Path, candidate_sha: str) -> Path:
    if not state_dir.is_absolute():
        raise ValueError("Phase266 runtime-state directory must be absolute")
    root = repository_root.resolve()
    state = state_dir.resolve()
    if state == root or root in state.parents:
        raise ValueError("Phase266 runtime-state directory must be outside repository root")
    candidate = _exact_hex(candidate_sha, 40, field="candidate SHA")
    return state / candidate / "phase266_runtime_state.json"


def _paper_payload(adapter: ProtectedCampaignRuntimeAdapter) -> dict[str, Any]:
    broker = adapter.paper_broker
    return {
        "fee_bps": str(broker.fee_bps),
        "slippage_bps": str(broker.slippage_bps),
        "fills": [
            {
                "side": fill.side,
                "qty": str(fill.qty),
                "price": str(fill.price),
                "fee": str(fill.fee),
                "latency_ms": int(fill.latency_ms),
                "status": fill.status,
                "reason": fill.reason,
            }
            for fill in broker.fills
        ],
        "positions": {
            symbol: {
                "symbol": position.symbol,
                "qty": str(position.qty),
                "entry_price": str(position.entry_price),
                "stop_loss": str(position.stop_loss),
                "take_profits": [str(value) for value in position.take_profits],
                "remaining_qty": str(position.remaining_qty),
                "realized_pnl": str(position.realized_pnl),
                "closed": bool(position.closed),
                "triggered_tps": sorted(int(value) for value in position.triggered_tps),
            }
            for symbol, position in sorted(broker.positions.items())
        },
    }


def _private_payload(adapter: ProtectedCampaignRuntimeAdapter) -> dict[str, Any]:
    projector = adapter.private_projector
    return {
        "seen_trades": sorted(str(value) for value in projector.seen_trades),
        "order_states": {str(key): str(value) for key, value in sorted(projector.order_states.items())},
        "order_progress": {
            str(key): [str(value[0]), str(value[1]), int(value[2])]
            for key, value in sorted(projector.order_progress.items())
        },
        "balances": {
            str(asset): [str(values[0]), str(values[1])]
            for asset, values in sorted(projector.balances.items())
        },
        "positions": {str(symbol): str(qty) for symbol, qty in sorted(projector.positions.items())},
        "terminated": bool(projector.terminated),
    }


def snapshot_runtime_state(
    adapter: ProtectedCampaignRuntimeAdapter,
    *,
    candidate_sha: str,
    environment_hash: str,
    topology_hash: str,
    telemetry_key: str,
    collection_last_record_sha256: str,
    now: datetime | None = None,
) -> dict[str, Any]:
    candidate = _exact_hex(candidate_sha, 40, field="candidate SHA")
    environment = _exact_hex(environment_hash, 64, field="acceptance environment hash")
    topology = _exact_hex(topology_hash, 64, field="topology hash")
    collection_hash = _exact_hex(collection_last_record_sha256, 64, field="collection last-record SHA-256")
    key = _key_bytes(telemetry_key)
    payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "classification": CLASSIFICATION,
        "candidate_sha": candidate,
        "acceptance_environment_id_hash": environment,
        "topology_hash": topology,
        "telemetry_key_id": hashlib.sha256(key).hexdigest(),
        "collection_last_record_sha256": collection_hash,
        "updated_at": _iso(now or _utc_now()),
        "paper": _paper_payload(adapter),
        "private": _private_payload(adapter),
        "shadow_halted": bool(getattr(adapter, "_shadow_halted", False)),
        "live_enabled": False,
        "production_ready": False,
    }
    digest = hmac.new(key, _canonical(payload), hashlib.sha256).hexdigest()
    payload["attestation"] = {"scheme": ATTESTATION_SCHEME, "sha256": digest}
    return payload


def write_runtime_state(
    path: Path,
    adapter: ProtectedCampaignRuntimeAdapter,
    *,
    candidate_sha: str,
    environment_hash: str,
    topology_hash: str,
    telemetry_key: str,
    collection_last_record_sha256: str,
    now: datetime | None = None,
) -> dict[str, Any]:
    payload = snapshot_runtime_state(
        adapter,
        candidate_sha=candidate_sha,
        environment_hash=environment_hash,
        topology_hash=topology_hash,
        telemetry_key=telemetry_key,
        collection_last_record_sha256=collection_last_record_sha256,
        now=now,
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)
    return payload


def _verify_payload(
    payload: dict[str, Any],
    *,
    candidate_sha: str,
    environment_hash: str,
    topology_hash: str,
    telemetry_key: str,
) -> None:
    if payload.get("schema_version") != SCHEMA_VERSION or payload.get("classification") != CLASSIFICATION:
        raise ValueError("Phase266 runtime-state schema/classification mismatch")
    expected = {
        "candidate_sha": _exact_hex(candidate_sha, 40, field="candidate SHA"),
        "acceptance_environment_id_hash": _exact_hex(environment_hash, 64, field="acceptance environment hash"),
        "topology_hash": _exact_hex(topology_hash, 64, field="topology hash"),
    }
    for field, value in expected.items():
        if payload.get(field) != value:
            raise ValueError(f"Phase266 runtime-state binding mismatch: {field}")
    if payload.get("live_enabled") is not False or payload.get("production_ready") is not False:
        raise ValueError("Phase266 runtime-state safety boundary is invalid")
    key = _key_bytes(telemetry_key)
    if payload.get("telemetry_key_id") != telemetry_key_id(telemetry_key):
        raise ValueError("Phase266 runtime-state telemetry key id mismatch")
    attestation = payload.get("attestation")
    if not isinstance(attestation, dict) or attestation.get("scheme") != ATTESTATION_SCHEME:
        raise ValueError("Phase266 runtime-state attestation is missing")
    unsigned = dict(payload)
    unsigned.pop("attestation", None)
    expected_digest = hmac.new(key, _canonical(unsigned), hashlib.sha256).hexdigest()
    actual = str(attestation.get("sha256", ""))
    if not hmac.compare_digest(actual, expected_digest):
        raise ValueError("Phase266 runtime-state HMAC verification failed")


def restore_runtime_state(
    path: Path,
    adapter: ProtectedCampaignRuntimeAdapter,
    *,
    candidate_sha: str,
    environment_hash: str,
    topology_hash: str,
    telemetry_key: str,
    current_collection_last_record_sha256: str | None = None,
) -> dict[str, Any] | None:
    if not path.exists():
        return None
    loaded = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        raise ValueError("Phase266 runtime-state root must be an object")
    payload = dict(loaded)
    _verify_payload(
        payload,
        candidate_sha=candidate_sha,
        environment_hash=environment_hash,
        topology_hash=topology_hash,
        telemetry_key=telemetry_key,
    )
    if current_collection_last_record_sha256 is not None:
        current_hash = _exact_hex(
            current_collection_last_record_sha256,
            64,
            field="current collection last-record SHA-256",
        )
        saved_hash = str(payload.get("collection_last_record_sha256", "")).lower()
        if saved_hash != current_hash:
            raise ValueError(
                "Phase266 runtime-state/collection checkpoint mismatch; refusing to guess paper/private continuity"
            )

    paper = payload.get("paper")
    private = payload.get("private")
    if not isinstance(paper, dict) or not isinstance(private, dict):
        raise ValueError("Phase266 runtime-state sections are missing")

    broker = adapter.paper_broker
    broker.fee_bps = Decimal(str(paper.get("fee_bps")))
    broker.slippage_bps = Decimal(str(paper.get("slippage_bps")))
    fills = paper.get("fills")
    positions = paper.get("positions")
    if not isinstance(fills, list) or not isinstance(positions, dict):
        raise ValueError("Phase266 paper runtime-state is invalid")
    broker.fills = [
        PaperFill(
            side=str(row["side"]),
            qty=Decimal(str(row["qty"])),
            price=Decimal(str(row["price"])),
            fee=Decimal(str(row["fee"])),
            latency_ms=int(row["latency_ms"]),
            status=str(row["status"]),
            reason=str(row["reason"]),
        )
        for row in fills
        if isinstance(row, dict)
    ]
    if len(broker.fills) != len(fills):
        raise ValueError("Phase266 paper fill state contains a non-object row")
    broker.positions = {}
    for symbol, raw in positions.items():
        if not isinstance(raw, dict):
            raise ValueError("Phase266 paper position state contains a non-object row")
        take_profits = tuple(Decimal(str(value)) for value in raw.get("take_profits", []))
        if len(take_profits) != 3:
            raise ValueError("Phase266 paper position must contain exactly three take-profits")
        broker.positions[str(symbol)] = PaperPosition(
            symbol=str(raw["symbol"]),
            qty=Decimal(str(raw["qty"])),
            entry_price=Decimal(str(raw["entry_price"])),
            stop_loss=Decimal(str(raw["stop_loss"])),
            take_profits=(take_profits[0], take_profits[1], take_profits[2]),
            remaining_qty=Decimal(str(raw["remaining_qty"])),
            realized_pnl=Decimal(str(raw["realized_pnl"])),
            closed=bool(raw["closed"]),
            triggered_tps={int(value) for value in raw.get("triggered_tps", [])},
        )

    projector = adapter.private_projector
    seen_trades = private.get("seen_trades")
    order_states = private.get("order_states")
    order_progress = private.get("order_progress")
    balances = private.get("balances")
    private_positions = private.get("positions")
    if not isinstance(seen_trades, list):
        raise ValueError("Phase266 private seen-trade state is invalid")
    if not isinstance(order_states, dict):
        raise ValueError("Phase266 private order-state section is invalid")
    if not isinstance(order_progress, dict):
        raise ValueError("Phase266 private order-progress section is invalid")
    if not isinstance(balances, dict):
        raise ValueError("Phase266 private balance section is invalid")
    if not isinstance(private_positions, dict):
        raise ValueError("Phase266 private position section is invalid")
    projector.seen_trades = {str(value) for value in seen_trades}
    projector.order_states = {str(key): str(value) for key, value in order_states.items()}
    projector.order_progress = {
        str(key): (str(value[0]), Decimal(str(value[1])), int(value[2]))
        for key, value in order_progress.items()
        if isinstance(value, list) and len(value) == 3
    }
    if len(projector.order_progress) != len(order_progress):
        raise ValueError("Phase266 private order-progress state is invalid")
    projector.balances = {
        str(asset): (Decimal(str(value[0])), Decimal(str(value[1])))
        for asset, value in balances.items()
        if isinstance(value, list) and len(value) == 2
    }
    if len(projector.balances) != len(balances):
        raise ValueError("Phase266 private balance state is invalid")
    projector.positions = {str(symbol): Decimal(str(qty)) for symbol, qty in private_positions.items()}
    projector.terminated = bool(private.get("terminated"))
    setattr(adapter, "_shadow_halted", bool(payload.get("shadow_halted")))
    return payload
