from __future__ import annotations
from dataclasses import dataclass
from decimal import Decimal
from collections import defaultdict

@dataclass(frozen=True)
class LedgerPosting:
    asset: str; amount: Decimal; reference_id: str

@dataclass(frozen=True)
class LedgerIntegrityResult:
    balanced: bool; imbalances: dict[str,Decimal]; duplicate_references: tuple[str,...]

def validate_double_entry(postings, *, tolerance=Decimal('0')):
    totals=defaultdict(lambda:Decimal('0')); refs=defaultdict(int)
    for p in postings:
        totals[p.asset]+=Decimal(str(p.amount)); refs[p.reference_id]+=1
    imbalances={a:v for a,v in totals.items() if abs(v)>tolerance}
    duplicates=tuple(sorted(k for k,v in refs.items() if v>2))
    return LedgerIntegrityResult(not imbalances and not duplicates,imbalances,duplicates)
