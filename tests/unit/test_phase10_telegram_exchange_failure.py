import pytest

from app.core.enums import RiskState
from app.execution.failure import ExchangeFailureCoordinator
from app.monitoring.telegram import TelegramBotClient
from app.risk.state import RiskMachine


class Response:
    def __init__(self, body, status=200): self.body=body; self.status=status
    def raise_for_status(self):
        if self.status >= 400: raise RuntimeError('http error')
    def json(self): return self.body


class Client:
    def __init__(self, response): self.response=response; self.calls=[]
    def post(self, url, json, timeout): self.calls.append((url,json,timeout)); return self.response


def test_telegram_bot_api_sends_message_without_exposing_token_in_payload():
    client=Client(Response({'ok':True,'result':{'message_id':42}}))
    bot=TelegramBotClient('SECRET_BOT_TOKEN','123',client=client)
    result=bot.send('Risk halted')
    assert result.delivered and result.message_id==42
    url,payload,_=client.calls[0]
    assert url.endswith('/sendMessage') and payload['chat_id']=='123' and payload['text']=='Risk halted'
    assert 'SECRET_BOT_TOKEN' not in str(payload)


def test_telegram_failure_error_does_not_leak_token():
    bot=TelegramBotClient('VERY_SECRET_TOKEN','123',client=Client(Response({},500)))
    with pytest.raises(RuntimeError) as exc: bot.send('hello')
    assert 'VERY_SECRET_TOKEN' not in str(exc.value)


def test_exchange_failure_halts_new_risk_checks_protection_alerts_and_reconnects():
    risk=RiskMachine(); seen=[]
    result=ExchangeFailureCoordinator(
        risk,
        protection_check=lambda: True,
        critical_alert=lambda msg: seen.append(('alert',msg)),
        reconnect=lambda: seen.append(('reconnect',True)),
    ).handle('BINANCE_DOWN')
    assert result.risk_state==RiskState.HALTED and risk.allow_new_risk() is False
    assert result.protection_verified and result.alert_delivered and result.reconnect_attempted
    assert [x[0] for x in seen]==['alert','reconnect']


def test_exchange_failure_stays_halted_even_if_protection_alert_or_reconnect_fails():
    risk=RiskMachine()
    boom=lambda *a,**k: (_ for _ in ()).throw(RuntimeError('down'))
    result=ExchangeFailureCoordinator(risk,protection_check=boom,critical_alert=boom,reconnect=boom).handle()
    assert risk.state==RiskState.HALTED and not risk.allow_new_risk()
    assert result.protection_verified is False and result.alert_delivered is False and result.reconnect_attempted is True
