from __future__ import annotations
from dataclasses import dataclass

ORDER=(
 'CAPITAL_AND_OPEN_POSITION_SAFETY',
 'EXCHANGE_ACCOUNT_REALITY_EXECUTION_CORRECTNESS',
 'DATA_INTEGRITY_POINT_IN_TIME_CORRECTNESS',
 'IDENTITY_SECRET_ACCESS_SECURITY',
 'ACCOUNTING_LEDGER_AUDIT_CORRECTNESS',
 'AVAILABILITY_PERFORMANCE_UX',
)

@dataclass(frozen=True)
class RequirementConflict:
    requirement_a: str
    requirement_b: str
    category_a: str
    category_b: str


def resolve_conflict(c:RequirementConflict)->str:
    try:
        ia=ORDER.index(c.category_a); ib=ORDER.index(c.category_b)
    except ValueError as exc:
        raise ValueError('unknown production-hardening precedence category') from exc
    if ia==ib: raise RuntimeError('same-priority conflict requires explicit ADR/human decision')
    return c.requirement_a if ia<ib else c.requirement_b
