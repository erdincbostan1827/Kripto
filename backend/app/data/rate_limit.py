from __future__ import annotations
from dataclasses import dataclass
import time

@dataclass
class Budget:
    limit:float; interval_seconds:float; used:float=0; window_started:float=0

class RateLimitBudget:
    def __init__(self): self.budgets={}
    def configure(self,key,limit,interval_seconds,now=None):
        if float(limit) <= 0 or float(interval_seconds) <= 0: raise ValueError('rate limit budget must be positive')
        self.budgets[key]=Budget(float(limit),float(interval_seconds),0,float(now if now is not None else time.time()))
    def allow(self,key,weight=1,priority='normal',now=None):
        now=float(now if now is not None else time.time()); b=self.budgets[key]
        if weight <= 0: raise ValueError('weight must be positive')
        if now < b.window_started: raise ValueError('rate-limit clock moved backwards')
        if now-b.window_started>=b.interval_seconds: b.used=0; b.window_started=now
        reserve=b.limit*.15 if priority=='low' else 0
        if b.used+weight>b.limit-reserve: return False
        b.used+=weight; return True
    def remaining(self,key): return max(0,self.budgets[key].limit-self.budgets[key].used)
    def exhausted(self,key,weight=1):
        b=self.budgets[key]
        return b.used+weight>b.limit
    def allow_with_fallback(self,primary_key,fallback_key,weight=1,now=None):
        """Consume primary budget, otherwise a separately capped REST fallback budget.

        Fallback never bypasses rate limiting: it has its own explicit finite
        budget and therefore fails closed when both budgets are exhausted.
        """
        if self.allow(primary_key,weight=weight,priority='normal',now=now):
            return 'PRIMARY'
        if fallback_key not in self.budgets:
            return None
        if self.allow(fallback_key,weight=weight,priority='normal',now=now):
            return 'FALLBACK'
        return None
