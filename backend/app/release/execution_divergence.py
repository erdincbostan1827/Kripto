from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass(frozen=True)
class ExecutionSample:
    fills: int
    fill_ratio: float
    mean_slippage_bps: float
    p95_ack_latency_ms: float
    reject_rate: float

    def __post_init__(self) -> None:
        if self.fills < 0:
            raise ValueError("fills cannot be negative")
        if not 0.0 <= self.fill_ratio <= 1.0:
            raise ValueError("fill_ratio must be in [0,1]")
        if self.mean_slippage_bps < 0:
            raise ValueError("mean_slippage_bps cannot be negative")
        if self.p95_ack_latency_ms < 0:
            raise ValueError("latency cannot be negative")
        if not 0.0 <= self.reject_rate <= 1.0:
            raise ValueError("reject_rate must be in [0,1]")


@dataclass(frozen=True)
class TestnetPaperDivergenceEvidence:
    paper: ExecutionSample
    testnet: ExecutionSample
    observed_at: datetime
    executed: bool
    real_testnet: bool
    evidence_reference: str

    def __post_init__(self) -> None:
        if self.observed_at.tzinfo is None:
            raise ValueError("observed_at must be timezone-aware")
        if not self.evidence_reference.strip():
            raise ValueError("evidence_reference required")

    def differences(self) -> dict[str, float]:
        return {
            "fill_ratio_delta": self.testnet.fill_ratio - self.paper.fill_ratio,
            "mean_slippage_bps_delta": self.testnet.mean_slippage_bps - self.paper.mean_slippage_bps,
            "p95_ack_latency_ms_delta": self.testnet.p95_ack_latency_ms - self.paper.p95_ack_latency_ms,
            "reject_rate_delta": self.testnet.reject_rate - self.paper.reject_rate,
        }

    def production_eligible(self) -> bool:
        return self.executed and self.real_testnet

    def to_final_evidence(self) -> dict[str, object]:
        return {
            "executed": self.executed,
            "real_testnet": self.real_testnet,
            "observed_at": self.observed_at.astimezone(timezone.utc).isoformat(),
            "paper": self.paper.__dict__,
            "testnet": self.testnet.__dict__,
            "differences": self.differences(),
            "evidence_reference": self.evidence_reference,
        }
