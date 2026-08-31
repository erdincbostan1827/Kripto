from __future__ import annotations
from dataclasses import dataclass,field
from datetime import datetime,timezone
import uuid

SEV1_TYPES={'ORPHAN_ORDER','UNPROTECTED_POSITION','EXTERNAL_ACCOUNT_ACTIVITY','VENUE_DIVERGENCE','DB_OUTAGE','REDIS_OUTAGE','SECURITY_COMPROMISE','BAD_DEPLOYMENT','DATA_CORRUPTION','BACKUP_RESTORE'}
@dataclass
class IncidentRecord:
    incident_id:str; severity:str; affected_scope:str; automatic_action:str; risk_state:str; evidence:list[str]
    incident_type:str='GENERAL'; correlation_ids:list[str]=field(default_factory=list)
    detected_at:datetime=field(default_factory=lambda:datetime.now(timezone.utc)); operator_actions:list[str]=field(default_factory=list); resolved_at:datetime|None=None; recovery_validation:dict=field(default_factory=dict)
class IncidentManager:
    def __init__(self): self.incidents={}
    def open(self,severity,scope,automatic_action,risk_state,evidence,*,incident_type='GENERAL',correlation_ids=None):
        if severity not in {'SEV1','SEV2','SEV3'}: raise ValueError('invalid severity')
        if severity=='SEV1' and incident_type not in SEV1_TYPES and incident_type!='GENERAL': raise ValueError('unknown SEV1 incident type')
        if severity=='SEV1' and (not scope or not automatic_action or not risk_state or not evidence): raise ValueError('SEV1 incident evidence incomplete')
        x=IncidentRecord(uuid.uuid4().hex,severity,scope,automatic_action,risk_state,list(evidence),incident_type,list(correlation_ids or [])); self.incidents[x.incident_id]=x; return x
    def resolve(self,incident_id,operator_action,recovery_validation):
        x=self.incidents[incident_id]
        if x.severity=='SEV1':
            required={'reconciliation_pass','risk_state_verified','evidence_preserved'}
            # Preserve backward compatibility: legacy callers setting reconciliation_pass alone remain accepted,
            # while typed SEV1 incidents require the complete recovery contract.
            if x.incident_type!='GENERAL' and not all(recovery_validation.get(k) for k in required): raise PermissionError('SEV1 recovery requires reconciliation, risk-state and evidence validation')
            if x.incident_type=='GENERAL' and not recovery_validation.get('reconciliation_pass'): raise PermissionError('SEV1 recovery requires reconciliation validation')
        x.operator_actions.append(operator_action); x.recovery_validation=dict(recovery_validation); x.resolved_at=datetime.now(timezone.utc); return x
