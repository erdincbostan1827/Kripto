from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Sequence

from app.research.time_validation import nested_walk_forward, purged_embargo_split
from app.research.validation import validate_research


def _fixture_total_return(xs: Sequence[float]) -> float:
    wealth = 1.0
    for value in xs:
        wealth *= 1.0 + float(value)
    return wealth - 1.0


@dataclass(frozen=True)
class LocalFixtureEvidence:
    """Deterministic local research evidence.

    This object proves research code paths and reporting invariants with local
    fixtures only.  It is deliberately not eligible to satisfy real-market
    PAPER/TESTNET/LIVE profitability release gates.  In particular, an IS/OOS
    split here demonstrates point-in-time validation mechanics, not investable
    performance.
    """

    classification: str
    in_sample_return: float
    out_of_sample_return: float
    walk_forward_folds: int
    purged_embargo_no_overlap: bool
    cost_adverse_scenarios: dict[str, float]
    effective_sample_size: float
    deflated_sharpe_ratio: float
    multiple_testing_adjusted_alpha: float
    tail_stress_scenarios: dict[str, float]
    benchmark_excess_return: float
    confidence_interval_95: tuple[float, float]
    strategy_regime_attribution: dict[str, float]
    execution_attribution: dict[str, float]
    accepted_under_fixture_thresholds: bool

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


def build_local_fixture_evidence(
    returns: Sequence[float],
    *,
    benchmark_returns: Sequence[float] | None = None,
) -> LocalFixtureEvidence:
    xs = [float(x) for x in returns]
    if len(xs) < 60:
        raise ValueError("at least 60 fixture returns are required")
    bench = [0.0] * len(xs) if benchmark_returns is None else [float(x) for x in benchmark_returns]
    if len(bench) != len(xs):
        raise ValueError("benchmark length must match returns")

    # Keep a final holdout and use strictly earlier validation folds.
    folds = nested_walk_forward(len(xs), initial_train=30, validation=10, step=10, final_holdout=10)
    if not folds:
        raise ValueError("fixture is too short for walk-forward evidence")

    split = purged_embargo_split(
        len(xs),
        train_end=30,
        validation_start=30,
        validation_end=45,
        purge=2,
        embargo=3,
    )
    no_overlap = not (
        set(split.train) & set(split.validation)
        or set(split.validation) & set(split.test)
        or set(split.train) & set(split.test)
    )

    oos = xs[-40:]
    ins = xs[:-40]
    wf = [sum(xs[i] for i in fold.validation) / len(fold.validation) for fold in folds]
    # Deterministic adverse scenarios: costs are applied to each observed return.
    fee = [x - 0.0004 for x in oos]
    slip = [x - 0.0005 for x in oos]
    latency = [x - 0.0002 for x in oos]
    funding = [x - 0.0003 for x in oos]
    parameter_low = [x - 0.0001 for x in oos]
    thirds = max(1, len(oos) // 3)
    regimes = {
        "bull": oos[:thirds],
        "bear": oos[thirds : 2 * thirds],
        "range": oos[2 * thirds :],
    }
    report = validate_research(
        in_sample_returns=ins,
        out_of_sample_returns=oos,
        walk_forward_returns=wf,
        benchmark_returns=bench[-40:],
        fee_scenarios={"adverse_fee": fee},
        slippage_scenarios={"adverse_slippage": slip},
        latency_scenarios={"adverse_latency": latency},
        parameter_scenarios={"minus_10pct": parameter_low},
        regime_returns=regimes,
        n_trials=5,
        min_trades=20,
        min_effective_samples=10,
        min_psr=0.0,
        min_dsr=0.0,
        seed=134,
    )
    gross_oos = _fixture_total_return(oos)
    fee_total = _fixture_total_return(fee)
    slip_total = _fixture_total_return(slip)
    latency_total = _fixture_total_return(latency)
    funding_total = _fixture_total_return(funding)

    # Tail scenarios are deterministic adverse transforms of the OOS fixture.
    # They exercise the reporting/gating code path without pretending to be a
    # calibrated market-tail model.
    tail_gap = [x - 0.015 if i == len(oos) // 2 else x for i, x in enumerate(oos)]
    liquidity_freeze = [min(x, 0.0) - 0.0025 for x in oos]
    volatility_shock = [x * 2.0 if x < 0 else x * 0.5 for x in oos]

    return LocalFixtureEvidence(
        classification="LOCAL_FIXTURE_ONLY_NOT_PRODUCTION_PROFITABILITY_EVIDENCE",
        in_sample_return=report.in_sample_return,
        out_of_sample_return=report.out_of_sample_return,
        walk_forward_folds=len(folds),
        purged_embargo_no_overlap=no_overlap,
        cost_adverse_scenarios={
            **{f"fee:{k}": v for k, v in report.fee_sensitivity.items()},
            **{f"slippage:{k}": v for k, v in report.slippage_sensitivity.items()},
            **{f"latency:{k}": v for k, v in report.latency_sensitivity.items()},
            "funding:adverse_funding": funding_total,
        },
        effective_sample_size=report.effective_sample_size,
        deflated_sharpe_ratio=report.deflated_sharpe_ratio,
        multiple_testing_adjusted_alpha=report.multiple_testing_adjusted_alpha,
        tail_stress_scenarios={
            "single_gap_shock": _fixture_total_return(tail_gap),
            "liquidity_freeze": _fixture_total_return(liquidity_freeze),
            "volatility_shock": _fixture_total_return(volatility_shock),
        },
        benchmark_excess_return=report.benchmark_excess_return,
        confidence_interval_95=report.bootstrap_ci95,
        strategy_regime_attribution=dict(report.regime_breakdown),
        execution_attribution={
            "gross_oos_return": gross_oos,
            "fee_drag": fee_total - gross_oos,
            "slippage_drag": slip_total - gross_oos,
            "latency_drag": latency_total - gross_oos,
            "funding_drag": funding_total - gross_oos,
        },
        accepted_under_fixture_thresholds=report.accepted,
    )
