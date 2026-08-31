import random
from decimal import Decimal
from app.risk.engine import size_position,effective_loss_per_unit
from app.core.money import normalize_quantity

def test_seeded_position_sizing_never_exceeds_risk_budget():
 rng=random.Random(20260826)
 for _ in range(1000):
  equity=Decimal(str(rng.uniform(100,100000))); entry=Decimal(str(rng.uniform(1,100000))); distance=entry*Decimal(str(rng.uniform(.001,.2))); stop=entry-distance; risk=Decimal(str(rng.uniform(.0001,.02))); step=Decimal('0.000001'); qty=size_position(equity,entry,stop,step,risk); assert qty*effective_loss_per_unit(entry,stop)<=equity*risk

def test_seeded_step_normalization_multiple():
 rng=random.Random(42); step=Decimal('0.001')
 for _ in range(1000):
  q=Decimal(str(rng.uniform(0,100))); n=normalize_quantity(q,step); assert n<=q and n%step==0
