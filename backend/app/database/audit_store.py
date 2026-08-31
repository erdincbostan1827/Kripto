from __future__ import annotations
from datetime import datetime,timezone
import hashlib,json,uuid
from sqlalchemy import select,text
from app.database.models import AuditLog
from app.core.storage_health import PersistentStorageUnavailable, classify_storage_failure


def _ts(dt:datetime)->str:
    if dt.tzinfo is None: dt=dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat().replace('+00:00','Z')

def _digest(previous_hash,actor,action,object_ref,correlation_id,created_at,reason,release_version):
    payload={'previous_hash':previous_hash,'actor':actor,'action':action,'object_ref':object_ref,'correlation_id':correlation_id,'timestamp':_ts(created_at),'reason':reason,'release_version':release_version}
    return hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(',',':')).encode()).hexdigest()

class DatabaseAuditStore:
    def __init__(self,session_factory,risk_machine=None): self.sf=session_factory; self.risk_machine=risk_machine
    def append(self,actor,action,object_ref,correlation_id,reason,release_version='0.3.0'):
        now=datetime.now(timezone.utc)
        with self.sf() as s:
            if s.bind and s.bind.dialect.name=='postgresql': s.execute(text("SELECT pg_advisory_xact_lock(91226051)"))
            prev=s.scalar(select(AuditLog.current_hash).order_by(AuditLog.created_at.desc(),AuditLog.id.desc()).limit(1)) or 'GENESIS'
            cur=_digest(prev,actor,action,object_ref,correlation_id,now,reason,release_version)
            row=AuditLog(id=uuid.uuid4().hex,previous_hash=prev,current_hash=cur,actor=actor,action=action,object_ref=object_ref,correlation_id=correlation_id,reason=reason,release_version=release_version,created_at=now)
            s.add(row)
            try:
                s.commit()
            except Exception as exc:
                try: s.rollback()
                except Exception:
                    rollback_failed = True
                failure=classify_storage_failure(exc)
                if self.risk_machine is not None:
                    self.risk_machine.halt(f'audit persistence failure: {failure.kind}')
                raise PersistentStorageUnavailable(f'{failure.kind}: durability-critical audit write failed') from exc
            return cur
    def verify(self):
        with self.sf() as s: rows=s.scalars(select(AuditLog).order_by(AuditLog.created_at,AuditLog.id)).all()
        prev='GENESIS'
        for row in rows:
            if row.previous_hash!=prev: return False
            expected=_digest(prev,row.actor,row.action,row.object_ref,row.correlation_id,row.created_at,row.reason,row.release_version)
            if expected!=row.current_hash: return False
            prev=row.current_hash
        return True
