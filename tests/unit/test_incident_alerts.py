import pytest
from app.core.incident import IncidentManager
from app.monitoring.alerts import AlertFanout

def test_sev1_requires_recovery_validation():
 m=IncidentManager(); x=m.open('SEV1','account:1','HALT','HALTED',['c1'])
 with pytest.raises(PermissionError): m.resolve(x.incident_id,'checked',{})
def test_sev1_resolution():
 m=IncidentManager(); x=m.open('SEV1','account:1','HALT','HALTED',['c1']); y=m.resolve(x.incident_id,'checked',{'reconciliation_pass':True}); assert y.resolved_at
def test_alert_fallback():
 seen=[]; f=AlertFanout({'telegram':lambda m:(_ for _ in ()).throw(RuntimeError('down')),'webhook':lambda m:seen.append(m)}); r=f.send('critical',critical=True); assert seen and any(x.delivered for x in r)
def test_all_critical_channels_failed():
 f=AlertFanout({'a':lambda m:(_ for _ in ()).throw(RuntimeError('down'))})
 with pytest.raises(RuntimeError): f.send('critical',critical=True)
