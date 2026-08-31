import pytest
from pydantic import ValidationError
from app.core.config import Settings
from app.core.enums import TradingMode,Environment

def test_defaults_paper(): assert Settings().mode==TradingMode.PAPER
@pytest.mark.parametrize('tf',['1m','3m','5m','15m','30m','1h','4h','1d'])
def test_supported_timeframes(tf): assert Settings(analysis_timeframes=(tf,)).analysis_timeframes==(tf,)
def test_empty_timeframes_fail_fast():
    with pytest.raises(ValidationError): Settings(analysis_timeframes=())
def test_bad_tf_rejected():
    with pytest.raises(ValidationError): Settings(analysis_timeframes=('2h',))
@pytest.mark.parametrize('env',[Environment.DEV,Environment.TEST,Environment.STAGING])
def test_nonprod_live_forbidden(env):
    with pytest.raises(ValidationError): Settings(environment=env,mode=TradingMode.LIVE,live_trading_enabled=True)
def test_prod_live_needs_flag():
    with pytest.raises(ValidationError): Settings(environment=Environment.PROD,mode=TradingMode.LIVE)
def test_prod_live_can_construct_when_flag_true(): assert Settings(environment=Environment.PROD,mode=TradingMode.LIVE,live_trading_enabled=True).mode==TradingMode.LIVE
