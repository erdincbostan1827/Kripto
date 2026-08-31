from __future__ import annotations
from dataclasses import dataclass
from typing import Any

@dataclass(frozen=True)
class FinalEvidenceBundle:
    benchmark_buy_hold: dict[str,Any]
    fee_slippage_stress: dict[str,Any]
    paper_vs_backtest: dict[str,Any]
    testnet_vs_paper: dict[str,Any] | None
    unresolved_known_issues: tuple[str,...]
    dataset_fingerprint: str
    release_id: str

    def blockers(self)->tuple[str,...]:
        out=[]
        if not self.dataset_fingerprint: out.append('DATASET_FINGERPRINT_MISSING')
        if not self.release_id: out.append('RELEASE_ID_MISSING')
        if not self.benchmark_buy_hold: out.append('BENCHMARK_MISSING')
        if not self.fee_slippage_stress: out.append('COST_STRESS_MISSING')
        if not self.paper_vs_backtest: out.append('PAPER_BACKTEST_DIVERGENCE_MISSING')
        # Credentialed TESTNET is allowed to remain unavailable, but must never be fabricated.
        if self.testnet_vs_paper is not None and (self.testnet_vs_paper.get('executed') is not True or self.testnet_vs_paper.get('real_testnet') is not True):
            out.append('TESTNET_EVIDENCE_INVALID')
        return tuple(out)

    def production_blockers(self)->tuple[str,...]:
        out=list(self.blockers())
        if self.testnet_vs_paper is None: out.append('TESTNET_VS_PAPER_NOT_TESTED')
        if self.unresolved_known_issues: out.append('UNRESOLVED_KNOWN_ISSUES')
        return tuple(out)
