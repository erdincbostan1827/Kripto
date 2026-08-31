from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from itertools import combinations
from typing import Sequence

UTC=timezone.utc


def session_bucket(ts: datetime) -> str:
    h=ts.astimezone(UTC).hour
    if 0<=h<8: return "ASIA"
    if 8<=h<13: return "EUROPE"
    if 13<=h<21: return "US_OVERLAP"
    return "OFF_HOURS"


@dataclass(frozen=True)
class TimeRiskContext:
    utc_hour: int
    day_of_week: int
    weekend: bool
    session: str
    funding_window: bool
    scheduled_event_window: bool
    maintenance_window: bool
    websocket_rotation_due: bool


def build_time_risk_context(ts: datetime, *, funding_hours: Sequence[int]=(0,8,16), event_times: Sequence[datetime]=(), maintenance_windows: Sequence[tuple[datetime,datetime]]=(), websocket_connected_at: datetime|None=None, websocket_max_lifetime: timedelta=timedelta(hours=23,minutes=30)) -> TimeRiskContext:
    t=ts.astimezone(UTC); event=any(abs((t-e.astimezone(UTC)).total_seconds())<=1800 for e in event_times)
    maintenance=any(a.astimezone(UTC)<=t<=b.astimezone(UTC) for a,b in maintenance_windows)
    rotation=bool(websocket_connected_at and t-websocket_connected_at.astimezone(UTC)>=websocket_max_lifetime)
    return TimeRiskContext(t.hour,t.weekday(),t.weekday()>=5,session_bucket(t),t.hour in set(funding_hours),event,maintenance,rotation)


@dataclass(frozen=True)
class Split:
    train: tuple[int,...]
    validation: tuple[int,...]
    test: tuple[int,...]=()


def purged_embargo_split(n: int, train_end: int, validation_start: int, validation_end: int, *, purge: int=0, embargo: int=0) -> Split:
    if not (0 < train_end <= validation_start < validation_end <= n): raise ValueError("invalid temporal boundaries")
    train=tuple(range(0,max(0,train_end-purge)))
    validation=tuple(range(min(n,validation_start+purge),validation_end))
    test=tuple(range(min(n,validation_end+embargo),n))
    if set(train)&set(validation) or set(validation)&set(test): raise AssertionError("split leakage")
    return Split(train,validation,test)


def nested_walk_forward(n: int, *, initial_train: int, validation: int, step: int, final_holdout: int) -> tuple[Split,...]:
    holdout_start=n-final_holdout; folds=[]; end=initial_train
    while end+validation<=holdout_start:
        folds.append(Split(tuple(range(end)),tuple(range(end,end+validation)),()))
        end+=step
    return tuple(folds)


def cpcv_splits(n_groups: int, test_groups: int, *, embargo_groups: int=0) -> tuple[Split,...]:
    if not (1<=test_groups<n_groups): raise ValueError("invalid CPCV dimensions")
    out=[]
    groups=range(n_groups)
    for test in combinations(groups,test_groups):
        blocked=set(test)
        for g in test:
            blocked.update(range(max(0,g-embargo_groups),min(n_groups,g+embargo_groups+1)))
        train=tuple(g for g in groups if g not in blocked)
        out.append(Split(train,(),tuple(test)))
    return tuple(out)
