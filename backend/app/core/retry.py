from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime,timezone,timedelta
import random

@dataclass(frozen=True)
class RetryDecision:
    retryable: bool
    attempt: int
    next_attempt_at: datetime|None
    reason: str

class RetryPolicy:
    def __init__(self,max_attempts:int=5,base_seconds:float=1.0,max_seconds:float=60.0,jitter_fraction:float=.2):
        if max_attempts < 1 or base_seconds <= 0 or max_seconds < base_seconds: raise ValueError('invalid retry policy')
        self.max_attempts=max_attempts; self.base_seconds=base_seconds; self.max_seconds=max_seconds; self.jitter_fraction=jitter_fraction
    @staticmethod
    def classify(exc:Exception)->bool:
        # Contract/validation/auth errors do not become infinite retry loops.
        name=type(exc).__name__.lower(); msg=str(exc).lower()
        non_retry=('valueerror','permissionerror','authentication','validation','schema','forbidden','unauthorized')
        if any(x in name or x in msg for x in non_retry): return False
        return isinstance(exc,(TimeoutError,ConnectionError,OSError)) or 'temporar' in msg or 'rate limit' in msg
    def decide(self,exc:Exception,attempt:int,now:datetime|None=None,rng:random.Random|None=None)->RetryDecision:
        now=now or datetime.now(timezone.utc); retryable=self.classify(exc)
        if (not retryable) or attempt>=self.max_attempts: return RetryDecision(False,attempt,None,'NON_RETRYABLE' if not retryable else 'RETRY_BUDGET_EXHAUSTED')
        base=min(self.max_seconds,self.base_seconds*(2**max(0,attempt-1)))
        r=rng or random.Random(); jitter=base*self.jitter_fraction*r.random()
        return RetryDecision(True,attempt,now+timedelta(seconds=base+jitter),'RETRYABLE')
