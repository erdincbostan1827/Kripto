from __future__ import annotations
import time
SENSITIVE=('secret','password','token','api_key','authorization')
def sanitize_attributes(attrs:dict): return {k:v for k,v in attrs.items() if not any(s in k.lower() for s in SENSITIVE)}
class Span:
    def __init__(self,name,collector): self.name=name; self.collector=collector
    def __enter__(self): self.start=time.perf_counter(); return self
    def __exit__(self,*_): self.collector.append((self.name,(time.perf_counter()-self.start)*1000))
