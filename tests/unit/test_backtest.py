from datetime import datetime,timezone,timedelta
from decimal import Decimal
import math
from app.backtest.engine import run
from app.backtest.validation import walk_forward_splits,purged_embargo_split,monte_carlo,effective_sample_size
from app.backtest.stats import probabilistic_sharpe,deflated_sharpe,pbo_from_rankings

def candles(n=100):
 t=datetime(2025,1,1,tzinfo=timezone.utc); out=[]
 for i in range(n):
  p=Decimal('100')+Decimal(i)/10
  out.append({'open_time':t+timedelta(hours=i),'close_time':t+timedelta(hours=i+1),'open':p,'high':p+2,'low':p-1,'close':p+1,'volume':100,'closed':True,'atr':Decimal('1')})
 return out
def test_next_bar_entry_and_costs():
 r=run(candles(),lambda h:'BUY' if len(h)==20 else 'HOLD'); assert r.trades and r.trades[0].entry_time==candles()[20]['open_time'] and r.trades[0].fee>0
def test_intrabar_stop_priority():
 cs=candles(25); cs[21]['low']=Decimal('90'); cs[21]['high']=Decimal('120'); r=run(cs,lambda h:'BUY' if len(h)==20 else 'HOLD'); assert r.trades[0].exit_reason=='STOP'
def test_walk_forward_no_overlap():
 s=walk_forward_splits(100,60,10); assert len(s)==4 and max(s[0][0])<min(s[0][1])
def test_purged_embargo():
 tr,te=purged_embargo_split(100,50,60,2,3); assert 48 not in tr and 49 not in tr and 60 not in tr and 62 not in tr and te[0]==50
def test_monte_carlo_deterministic(): assert monte_carlo([.01,-.005,.02],100,42)==monte_carlo([.01,-.005,.02],100,42)
def test_monte_carlo_fields(): assert set(monte_carlo([.01,-.005],50))=={'expected_return','worst_drawdown','probability_of_ruin','ci95'}
def test_effective_sample_size_positive(): assert effective_sample_size([1,-1,1,-1,1])>=1
def test_psr_bounds(): assert 0<=probabilistic_sharpe(1,.5,100)<=1
def test_dsr_bounds(): assert 0<=deflated_sharpe(1,100,100)<=1
def test_pbo(): assert pbo_from_rankings([.1,.2],[.6,.4])==.5


def test_multi_asset_backtest_uses_point_in_time_universe_and_shared_equity_curve():
 from app.backtest.engine import run_multi_asset
 from app.universe.manager import UniverseMembership,PointInTimeUniverse
 cs1=candles(40); cs2=candles(40)
 listing=cs2[25]['open_time']
 u=PointInTimeUniverse([UniverseMembership('A',cs1[0]['open_time']),UniverseMembership('B',listing)])
 def signal(symbol,h):
  if symbol=='A' and len(h)==10: return 'BUY'
  if symbol=='B' and len(h)==10: return 'BUY'  # must be blocked: B is not listed yet
  if symbol=='B' and len(h)==26: return 'BUY'
  return 'HOLD'
 r=run_multi_asset({'A':cs1,'B':cs2},signal,universe_fn=u.members)
 assert r.equity_curve
 assert r.fees>=0 and r.slippage>=0
 assert not any(t.symbol=='B' and t.entry_time==cs2[10]['open_time'] for t in r.trades)


def test_multi_asset_delisting_forces_exit_and_costs_are_charged():
 from app.backtest.engine import run_multi_asset
 from app.universe.manager import UniverseMembership,PointInTimeUniverse
 cs=candles(30); de=cs[15]['open_time']; u=PointInTimeUniverse([UniverseMembership('A',cs[0]['open_time'],delisted_at=de)])
 r=run_multi_asset({'A':cs},lambda _s,h:'BUY' if len(h)==10 else 'HOLD',universe_fn=u.members)
 assert r.trades and r.trades[0].exit_reason=='UNIVERSE_EXIT'
 assert r.trades[0].fee>0 and r.trades[0].slippage>0
