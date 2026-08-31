from __future__ import annotations
from datetime import datetime,timezone,timedelta
import uuid,random
from .dlq_operator import payload_hash
from .models import OutboxEvent,DeadLetterRow
class OutboxDispatcher:
    def __init__(self,session_factory,publisher,max_attempts=5): self.sf=session_factory; self.publisher=publisher; self.max_attempts=max_attempts
    def dispatch_once(self,now=None):
        now=now or datetime.now(timezone.utc); published=failed=0
        with self.sf() as s:
            rows=s.query(OutboxEvent).filter(OutboxEvent.published_at.is_(None)).all()
            for row in rows:
                if row.next_attempt_at and row.next_attempt_at>now: continue
                try: self.publisher(row.topic,row.payload); row.published_at=now; published+=1
                except Exception as exc:
                    row.attempts+=1; row.last_error=str(exc); failed+=1
                    if row.attempts>=self.max_attempts:
                        if not s.query(DeadLetterRow).filter_by(original_event_id=row.event_id).first(): s.add(DeadLetterRow(id=uuid.uuid4().hex,original_event_id=row.event_id,event_type=row.topic,schema_version=1,payload_hash=payload_hash(row.payload),failure_reason=str(exc),correlation_id='',attempts=row.attempts,consumer_version='0.3.0-local-acceptance',first_failed_at=now,last_failed_at=now,resolution_state='OPEN'))
                        row.published_at=now
                    else: row.next_attempt_at=now+timedelta(seconds=min(60,2**row.attempts)+random.random())
            s.commit()
        return {'published':published,'failed':failed}
