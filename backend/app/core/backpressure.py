from __future__ import annotations
from dataclasses import dataclass
import heapq,itertools
PRIORITY={'private_order_fill':0,'protective_position':1,'best_bid_ask':2,'active_position_market':3,'candidate_market':4,'scanner_low':5}
@dataclass(frozen=True)
class QueuedEvent: category:str; payload:object
class PriorityEventBuffer:
    def __init__(self,maxsize=1024): self.maxsize=maxsize; self._heap=[]; self._counter=itertools.count(); self.dropped=0
    def put(self,event:QueuedEvent):
        item=(PRIORITY[event.category],next(self._counter),event)
        if len(self._heap)<self.maxsize: heapq.heappush(self._heap,item); return True
        worst=max(self._heap,key=lambda x:(x[0],x[1]))
        if item[0]<worst[0]: self._heap.remove(worst); heapq.heapify(self._heap); heapq.heappush(self._heap,item); self.dropped+=1; return True
        self.dropped+=1; return False
    def get(self): return heapq.heappop(self._heap)[2]
    def __len__(self): return len(self._heap)
