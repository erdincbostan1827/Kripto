from __future__ import annotations

import gc
import json
import sys
import time
import tracemalloc
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.core.backpressure import PriorityEventBuffer, QueuedEvent
from app.execution.service import ExecutionService
from app.exchange.mock import MockExchange
from app.exchange.models import OrderIntent
from app.risk.state import RiskMachine
from app.signals.multi_timeframe import analyze_multi_timeframe

REPORT = ROOT / "reports/LOAD_SOAK_REPORT.md"


def run_load_soak(
    *,
    duplicate_submits: int = 5000,
    event_messages: int = 5000,
    mtf_cycles: int = 36,
    memory_cycles: int = 24,
    retained_memory_budget_bytes: int = 2_000_000,
) -> dict[str, object]:
    started = time.perf_counter()

    exchange = MockExchange()
    service = ExecutionService(exchange, RiskMachine())
    intent = OrderIntent("load-intent-1", "acct", "BTCUSDT", "BUY", "LIMIT", Decimal("0.01"), Decimal("60000"))
    idempotency_start = time.perf_counter()
    for _ in range(duplicate_submits):
        service.submit(intent, Decimal("60000"), Decimal("100"))
    idempotency_seconds = time.perf_counter() - idempotency_start
    if len(exchange.orders) != 1:
        raise AssertionError("duplicate intent produced more than one exchange order")

    buffer = PriorityEventBuffer(maxsize=128)
    buffer_start = time.perf_counter()
    for i in range(event_messages):
        category = "private_order_fill" if i % 100 == 0 else "scanner_low"
        buffer.put(QueuedEvent(category, {"sequence": i}))
        if len(buffer) > 128:
            raise AssertionError("bounded event buffer exceeded maxsize")
    buffer_seconds = time.perf_counter() - buffer_start

    mtf_candles = {tf: exchange.get_klines("BTCUSDT", tf, 260) for tf in ("1d", "4h", "1h", "15m", "5m")}
    mtf_start = time.perf_counter()
    mtf_decisions = [analyze_multi_timeframe(mtf_candles) for _ in range(mtf_cycles)]
    mtf_seconds = time.perf_counter() - mtf_start
    if len(mtf_decisions) != mtf_cycles:
        raise AssertionError("MTF load cycle incomplete")
    del mtf_decisions

    # Warm caches before measuring retained application allocations.  The goal is
    # a bounded local leak sentinel, not a production/browser capacity claim.
    for _ in range(4):
        analyze_multi_timeframe(mtf_candles)
    gc.collect()
    tracemalloc.start()
    before = tracemalloc.take_snapshot()
    for _ in range(memory_cycles):
        analyze_multi_timeframe(mtf_candles)
    gc.collect()
    after = tracemalloc.take_snapshot()
    retained_growth = sum(max(0, stat.size_diff) for stat in after.compare_to(before, "filename"))
    tracemalloc.stop()
    if retained_growth > retained_memory_budget_bytes:
        raise AssertionError(
            f"retained memory growth exceeded budget: {retained_growth} > {retained_memory_budget_bytes}"
        )

    elapsed = time.perf_counter() - started
    return {
        "profile": "LOCAL_MOCK_PAPER",
        "status": "PASS",
        "duplicate_submits": duplicate_submits,
        "exchange_orders_created": len(exchange.orders),
        "idempotency_seconds": round(idempotency_seconds, 6),
        "event_messages": event_messages,
        "event_queue_max": 128,
        "event_queue_final": len(buffer),
        "event_dropped": buffer.dropped,
        "buffer_seconds": round(buffer_seconds, 6),
        "mtf_cycles": mtf_cycles,
        "mtf_seconds": round(mtf_seconds, 6),
        "memory_cycles": memory_cycles,
        "retained_memory_growth_bytes": retained_growth,
        "retained_memory_budget_bytes": retained_memory_budget_bytes,
        "memory_leak_sentinel": "PASS",
        "elapsed_seconds": round(elapsed, 6),
    }


def main() -> None:
    payload = run_load_soak()
    REPORT.write_text(
        "# Load / Soak Acceptance Report\n\n"
        "Status: **PASS — LOCAL MOCK/PAPER SAFETY INVARIANTS ONLY**\n\n"
        "This includes a bounded Python retained-memory leak sentinel for the local MOCK/PAPER workload. "
        "It is not a production capacity benchmark and does not validate exchange, network, database, Redis, browser or multi-day soak behavior.\n\n"
        "```json\n" + json.dumps(payload, indent=2) + "\n```\n",
        encoding="utf-8",
    )
    print(json.dumps(payload))


if __name__ == "__main__":
    main()
