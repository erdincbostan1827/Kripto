import json, logging
from app.core.logging import JsonFormatter,redact


def test_recursive_redaction_removes_sensitive_values():
    x=redact({'api_key':'abc','nested':{'password':'p','safe':1},'token_value':'x'})
    assert x['api_key']=='[REDACTED]' and x['nested']['password']=='[REDACTED]' and x['nested']['safe']==1 and x['token_value']=='[REDACTED]'

def test_json_formatter_contains_correlation_without_secret_details():
    record=logging.LogRecord('ctp',logging.ERROR,__file__,1,'failed',(),None)
    record.correlation_id='c1'; record.details={'password':'do-not-log','symbol':'BTCUSDT'}
    data=json.loads(JsonFormatter().format(record))
    assert data['correlation_id']=='c1' and data['details']['password']=='[REDACTED]' and data['details']['symbol']=='BTCUSDT'
