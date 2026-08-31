from __future__ import annotations
from dataclasses import dataclass,field
from datetime import datetime,timezone
@dataclass(frozen=True)
class ResearchTrial:
    trial_id:str; universe_version:str; strategy_version:str; parameter_space:dict; feature_set:tuple[str,...]; timeframe_set:tuple[str,...]; train_window:tuple[str,str]; oos_window:tuple[str,str]; primary_metric:str; outcome:dict; created_at:datetime=field(default_factory=lambda:datetime.now(timezone.utc))
class ResearchRegistry:
    def __init__(self): self._trials=[]
    def append(self,trial:ResearchTrial):
        if any(x.trial_id==trial.trial_id for x in self._trials): raise ValueError('trial id immutable/duplicate')
        self._trials.append(trial); return trial
    def all(self): return tuple(self._trials)
    def failed(self): return tuple(x for x in self._trials if not x.outcome.get('accepted',False))

# Phase 103 append-only research hypothesis/trial ledger.
import hashlib
import json
import re
import math
from typing import Any

_HASH_RE = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True)
class ResearchHypothesis:
    hypothesis_id: str
    statement: str
    primary_metric: str
    test_set_hash: str
    parameter_search_budget: int
    researcher_agent: str
    registered_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        if any(not str(value).strip() for value in (self.hypothesis_id, self.statement, self.primary_metric, self.researcher_agent)):
            raise ValueError("hypothesis pre-registration fields are required")
        if not _HASH_RE.fullmatch(self.test_set_hash):
            raise ValueError("test_set_hash must be sha256")
        if self.parameter_search_budget < 1:
            raise ValueError("parameter_search_budget must be positive")
        if self.registered_at.tzinfo is None:
            raise ValueError("registered_at must be timezone-aware")


@dataclass(frozen=True)
class ResearchTrialLedgerEntry:
    trial_id: str
    hypothesis_id: str
    strategy_family: str
    tested_features: tuple[str, ...]
    tested_parameters: dict[str, Any]
    dataset_hash: str
    train_period: tuple[datetime, datetime]
    validation_period: tuple[datetime, datetime]
    test_period: tuple[datetime, datetime]
    metrics: dict[str, float]
    failure_reason: str | None
    selected: bool
    researcher_agent: str
    timestamp: datetime
    primary_metric: str
    test_set_hash: str
    parameter_search_budget: int
    search_ordinal: int
    previous_hash: str
    entry_hash: str


class ResearchTrialLedger:
    GENESIS_HASH = "0" * 64

    def __init__(self) -> None:
        self._hypotheses: dict[str, ResearchHypothesis] = {}
        self._entries: list[ResearchTrialLedgerEntry] = []

    def register_hypothesis(self, hypothesis: ResearchHypothesis) -> ResearchHypothesis:
        if hypothesis.hypothesis_id in self._hypotheses:
            raise ValueError("hypothesis id immutable/duplicate")
        self._hypotheses[hypothesis.hypothesis_id] = hypothesis
        return hypothesis

    @staticmethod
    def _periods_valid(*periods: tuple[datetime, datetime]) -> bool:
        if any(start.tzinfo is None or end.tzinfo is None or start >= end for start, end in periods):
            return False
        train, validation, test = periods
        return train[1] <= validation[0] and validation[1] <= test[0]

    @staticmethod
    def _hash_payload(payload: dict[str, Any]) -> str:
        raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
        return hashlib.sha256(raw).hexdigest()

    def append_trial(
        self,
        *,
        trial_id: str,
        hypothesis_id: str,
        strategy_family: str,
        tested_features: tuple[str, ...],
        tested_parameters: dict[str, Any],
        dataset_hash: str,
        train_period: tuple[datetime, datetime],
        validation_period: tuple[datetime, datetime],
        test_period: tuple[datetime, datetime],
        metrics: dict[str, float],
        failure_reason: str | None,
        selected: bool,
        researcher_agent: str,
        timestamp: datetime,
        primary_metric: str,
        test_set_hash: str,
    ) -> ResearchTrialLedgerEntry:
        if any(entry.trial_id == trial_id for entry in self._entries):
            raise ValueError("trial id immutable/duplicate")
        hypothesis = self._hypotheses.get(hypothesis_id)
        if hypothesis is None:
            raise PermissionError("hypothesis must be registered before trial result")
        if timestamp.tzinfo is None or timestamp < hypothesis.registered_at:
            raise PermissionError("trial result cannot predate hypothesis registration")
        if primary_metric != hypothesis.primary_metric:
            raise PermissionError("primary metric is locked by pre-registration")
        if test_set_hash != hypothesis.test_set_hash:
            raise PermissionError("test set is locked by pre-registration")
        search_ordinal = 1 + sum(entry.hypothesis_id == hypothesis_id for entry in self._entries)
        if search_ordinal > hypothesis.parameter_search_budget:
            raise PermissionError("parameter search budget exceeded")
        if not trial_id.strip() or not strategy_family.strip() or not researcher_agent.strip():
            raise ValueError("trial identity fields are required")
        if not tested_features or not isinstance(tested_parameters, dict) or not tested_parameters:
            raise ValueError("tested features and parameters are required")
        if not _HASH_RE.fullmatch(dataset_hash) or not _HASH_RE.fullmatch(test_set_hash):
            raise ValueError("dataset/test hashes must be sha256")
        if not self._periods_valid(train_period, validation_period, test_period):
            raise ValueError("train/validation/test periods must be ordered and non-overlapping")
        if not metrics:
            raise ValueError("trial metrics are required")
        if any(not math.isfinite(float(value)) for value in metrics.values()):
            raise ValueError("trial metrics must be finite")
        if not selected and not (failure_reason or "").strip():
            raise ValueError("rejected trial requires failure_reason")
        if selected and failure_reason:
            raise ValueError("selected trial cannot have failure_reason")

        previous_hash = self._entries[-1].entry_hash if self._entries else self.GENESIS_HASH
        payload = {
            "trial_id": trial_id,
            "hypothesis_id": hypothesis_id,
            "strategy_family": strategy_family,
            "tested_features": tested_features,
            "tested_parameters": tested_parameters,
            "dataset_hash": dataset_hash,
            "train_period": train_period,
            "validation_period": validation_period,
            "test_period": test_period,
            "metrics": metrics,
            "failure_reason": failure_reason,
            "selected": selected,
            "researcher_agent": researcher_agent,
            "timestamp": timestamp,
            "primary_metric": primary_metric,
            "test_set_hash": test_set_hash,
            "parameter_search_budget": hypothesis.parameter_search_budget,
            "search_ordinal": search_ordinal,
            "previous_hash": previous_hash,
        }
        entry_hash = self._hash_payload(payload)
        entry = ResearchTrialLedgerEntry(**payload, entry_hash=entry_hash)
        self._entries.append(entry)
        return entry

    def all(self) -> tuple[ResearchTrialLedgerEntry, ...]:
        return tuple(self._entries)

    def hypotheses(self) -> tuple[ResearchHypothesis, ...]:
        return tuple(self._hypotheses.values())

    def verify_integrity(self) -> bool:
        previous = self.GENESIS_HASH
        for entry in self._entries:
            payload = {name: getattr(entry, name) for name in entry.__dataclass_fields__ if name != "entry_hash"}
            if entry.previous_hash != previous or self._hash_payload(payload) != entry.entry_hash:
                return False
            previous = entry.entry_hash
        return True
