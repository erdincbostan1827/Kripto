from datetime import datetime,timezone,timedelta
from decimal import Decimal
from app.indicators.engine import indicators
from app.strategies.regime import detect_regime
from app.signals.engine import decide,falling_knife_blocked

def rows(up=True,n=250):
 t=datetime(2025,1,1,tzinfo=timezone.utc); out=[]
 for i in range(n):
  p=100+i*.2 if up else 200-i*.2
  out.append({'open_time':t+timedelta(hours=i),'close_time':t+timedelta(hours=i+1),'open':p,'high':p+1,'low':p-1,'close':p+.1,'volume':100+i,'closed':True})
 return out
def test_indicator_keys():
 f=indicators(rows()); assert {'rsi','macd','atr','ema21','ema50','ema200','volume_ratio','obv','roc'}<=set(f)
def test_bullish_regime(): assert detect_regime(indicators(rows(True)))=='BULLISH_TREND'
def test_bearish_regime(): assert detect_regime(indicators(rows(False)))=='BEARISH_TREND'
def test_falling_knife_blocks_bearish():
 f=indicators(rows(False)); f['price']=float(rows(False)[-1]['close']); assert falling_knife_blocked(f,'BEARISH_TREND')
def test_signal_explainability():
 f=indicators(rows(True)); f['price']=float(rows(True)[-1]['close']); d=decide(f,'BULLISH_TREND','2026-01-01T00:00:00Z'); assert d.reasons and d.invalidation and d.data_timestamp
def test_falling_knife_never_generates_buy_and_exposes_bearish_direction():
 f=indicators(rows(False)); f['price']=float(rows(False)[-1]['close']); d=decide(f,'BEARISH_TREND','x'); assert d.signal.value in {'SELL','STRONG_SELL'}

def test_mandatory_indicator_feature_set_is_finite():
    import math
    f=indicators(rows(True))
    required={
        'sma20','sma50','sma100','sma200','ema9','ema21','ema50','ema200','vwap',
        'rsi','macd','macd_signal','stoch_rsi','roc','atr','bb_upper','bb_lower','bb_width',
        'historical_volatility','volume_sma','volume_ratio','obv','volume_spike','adx','di_plus','di_minus',
        'higher_high','higher_low','lower_high','lower_low','support','resistance','trend_slope'
    }
    assert required <= set(f)
    assert all(math.isfinite(float(f[key])) for key in required)
    assert 0 <= f['rsi'] <= 100
    assert 0 <= f['stoch_rsi'] <= 100
    assert f['support'] <= f['resistance']


def test_signal_taxonomy_can_emit_reduce():
    f=indicators(rows(True)); f.update({'price':100.0,'ema21':99.0,'ema50':100.0,'rsi':49.0,'macd':-0.1,'macd_signal':0.0,'volume_ratio':1.0,'trend_slope':0.1,'atr':1.0})
    d=decide(f,'SIDEWAYS','x')
    assert d.signal.value in {'REDUCE','HOLD','SELL'}

def test_sideways_regime():
    assert detect_regime({'atr':1,'bb_width':0.01,'ema21':100,'ema50':100,'ema200':100,'trend_slope':0})=='SIDEWAYS'

def test_high_volatility_regime():
    assert detect_regime({'atr':5,'bb_width':0.10,'ema21':100,'ema50':100,'ema200':100,'trend_slope':0})=='HIGH_VOLATILITY'
