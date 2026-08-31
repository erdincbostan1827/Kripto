from __future__ import annotations
from dataclasses import dataclass
from decimal import Decimal
import math
@dataclass(frozen=True)
class Trade:
    entry_time:object; exit_time:object; side:str; qty:Decimal; entry:Decimal; exit:Decimal; fee:Decimal; slippage:Decimal; pnl:Decimal; exit_reason:str; symbol:str=''
@dataclass(frozen=True)
class BacktestResult:
    trades:list[Trade]; total_return:float; max_drawdown:float; win_rate:float; profit_factor:float; expectancy:float

def run(candles:list[dict],signal_fn,initial_equity=Decimal('10000'),risk_fraction=Decimal('0.0025'),fee_bps=Decimal('10'),slippage_bps=Decimal('5'),spread_bps=Decimal('5')):
    equity=Decimal(initial_equity); peak=equity; maxdd=Decimal('0'); trades=[]; pos=None
    for i in range(1,len(candles)):
        prev=candles[i-1]; bar=candles[i]; signal=signal_fn(candles[:i])
        if pos is None and signal=='BUY':
            entry=Decimal(str(bar['open']))*(Decimal('1')+(spread_bps/2+slippage_bps)/Decimal(10000)); atr=Decimal(str(prev.get('atr', max(Decimal(str(prev['high']))-Decimal(str(prev['low'])),Decimal('0.01'))))); stop=entry-atr*2
            risk_per_unit=entry-stop+entry*(fee_bps*2+spread_bps+slippage_bps*2)/Decimal(10000); qty=equity*risk_fraction/risk_per_unit
            pos={'entry':entry,'stop':stop,'tp':entry+(entry-stop)*2,'qty':qty,'time':bar['open_time']}
        elif pos:
            low,high=Decimal(str(bar['low'])),Decimal(str(bar['high'])); exit_price=None; reason=None
            if low<=pos['stop']: exit_price=pos['stop']*(Decimal('1')-slippage_bps/Decimal(10000)); reason='STOP'
            elif high>=pos['tp']: exit_price=pos['tp']*(Decimal('1')-slippage_bps/Decimal(10000)); reason='TP'
            elif signal=='SELL': exit_price=Decimal(str(bar['open']))*(Decimal('1')-(spread_bps/2+slippage_bps)/Decimal(10000)); reason='SIGNAL'
            if exit_price:
                notional=(pos['entry']+exit_price)*pos['qty']; fee=notional*fee_bps/Decimal(10000); slip=notional*slippage_bps/Decimal(10000); pnl=(exit_price-pos['entry'])*pos['qty']-fee; equity+=pnl; trades.append(Trade(pos['time'],bar['open_time'],'LONG',pos['qty'],pos['entry'],exit_price,fee,slip,pnl,reason)); pos=None
        peak=max(peak,equity); maxdd=max(maxdd,(peak-equity)/peak if peak else Decimal('0'))
    pnls=[float(t.pnl) for t in trades]; wins=[x for x in pnls if x>0]; losses=[x for x in pnls if x<0]; pf=sum(wins)/abs(sum(losses)) if losses else (float('inf') if wins else 0.0)
    return BacktestResult(trades,float((equity-Decimal(initial_equity))/Decimal(initial_equity)),float(maxdd),len(wins)/len(pnls) if pnls else 0.0,pf,sum(pnls)/len(pnls) if pnls else 0.0)

@dataclass(frozen=True)
class PortfolioBacktestResult:
    trades:list[Trade]
    equity_curve:list[tuple[object,float]]
    total_return:float
    max_drawdown:float
    fees:float
    slippage:float
    symbols_traded:tuple[str,...]


def run_multi_asset(
    candles_by_symbol:dict[str,list[dict]],
    signal_fn,
    *,
    universe_fn=None,
    initial_equity=Decimal('10000'),
    risk_fraction=Decimal('0.0025'),
    fee_bps=Decimal('10'),
    slippage_bps=Decimal('5'),
    spread_bps=Decimal('5'),
    max_positions:int=5,
):
    """Shared-equity, next-bar, long-only portfolio backtest.

    The universe is evaluated at each decision timestamp, preventing future
    listings/delisted instruments from leaking into historical selection.
    Same-bar stop/TP ambiguity remains pessimistic: stop wins.
    """
    symbols=tuple(sorted(candles_by_symbol))
    by_time:dict[object,list[tuple[str,int]]]={}
    for symbol,rows in candles_by_symbol.items():
        for i in range(1,len(rows)):
            by_time.setdefault(rows[i]['open_time'],[]).append((symbol,i))
    equity=Decimal(initial_equity); peak=equity; maxdd=Decimal('0'); positions={}; trades=[]; curve=[]
    for ts in sorted(by_time):
        active=set(symbols if universe_fn is None else universe_fn(ts))
        # Exit first, so shared capital/risk is deterministic and conservative.
        for symbol,i in sorted(by_time[ts]):
            if symbol not in positions: continue
            bar=candles_by_symbol[symbol][i]; history=candles_by_symbol[symbol][:i]; pos=positions[symbol]
            low,high=Decimal(str(bar['low'])),Decimal(str(bar['high'])); signal=signal_fn(symbol,history)
            exit_price=None; reason=None
            if symbol not in active:
                exit_price=Decimal(str(bar['open']))*(Decimal('1')-(spread_bps/2+slippage_bps)/Decimal(10000)); reason='UNIVERSE_EXIT'
            elif low<=pos['stop']:
                exit_price=pos['stop']*(Decimal('1')-slippage_bps/Decimal(10000)); reason='STOP'
            elif high>=pos['tp']:
                exit_price=pos['tp']*(Decimal('1')-slippage_bps/Decimal(10000)); reason='TP'
            elif signal=='SELL':
                exit_price=Decimal(str(bar['open']))*(Decimal('1')-(spread_bps/2+slippage_bps)/Decimal(10000)); reason='SIGNAL'
            if exit_price is not None:
                notional=(pos['entry']+exit_price)*pos['qty']; fee=notional*fee_bps/Decimal(10000); slip=notional*slippage_bps/Decimal(10000)
                pnl=(exit_price-pos['entry'])*pos['qty']-fee; equity+=pnl
                trades.append(Trade(pos['time'],bar['open_time'],'LONG',pos['qty'],pos['entry'],exit_price,fee,slip,pnl,reason,symbol)); del positions[symbol]
        for symbol,i in sorted(by_time[ts]):
            if symbol in positions or symbol not in active or len(positions)>=max_positions: continue
            rows=candles_by_symbol[symbol]; prev=rows[i-1]; bar=rows[i]; history=rows[:i]
            if signal_fn(symbol,history)!='BUY': continue
            entry=Decimal(str(bar['open']))*(Decimal('1')+(spread_bps/2+slippage_bps)/Decimal(10000))
            atr=Decimal(str(prev.get('atr',max(Decimal(str(prev['high']))-Decimal(str(prev['low'])),Decimal('0.01')))))
            stop=entry-atr*2; risk_per_unit=entry-stop+entry*(fee_bps*2+spread_bps+slippage_bps*2)/Decimal(10000)
            qty=equity*risk_fraction/risk_per_unit
            positions[symbol]={'entry':entry,'stop':stop,'tp':entry+(entry-stop)*2,'qty':qty,'time':bar['open_time']}
        peak=max(peak,equity); maxdd=max(maxdd,(peak-equity)/peak if peak else Decimal('0')); curve.append((ts,float(equity)))
    total_fees=sum((t.fee for t in trades),Decimal('0')); total_slippage=sum((t.slippage for t in trades),Decimal('0'))
    return PortfolioBacktestResult(trades,curve,float((equity-Decimal(initial_equity))/Decimal(initial_equity)),float(maxdd),float(total_fees),float(total_slippage),tuple(sorted({s for s in symbols if any(t.entry_time in {r['open_time'] for r in candles_by_symbol[s]} for t in trades)})))
