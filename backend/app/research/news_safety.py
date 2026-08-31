from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from typing import Iterable, Mapping

UTC = timezone.utc


@dataclass(frozen=True)
class NewsRecord:
    source_id: str
    source_url: str
    story_id: str
    publication_time: datetime
    ingestion_time: datetime
    language: str
    text: str
    source_reliability: float
    version: int = 1
    parent_story_id: str | None = None

    def __post_init__(self) -> None:
        if not self.source_id or not self.source_url or not self.story_id:
            raise ValueError("source/story identity required")
        if not (0.0 <= self.source_reliability <= 1.0):
            raise ValueError("source_reliability must be bounded")
        if self.version < 1:
            raise ValueError("version must be positive")
        if self.ingestion_time < self.publication_time:
            raise ValueError("ingestion cannot predate publication")


@dataclass(frozen=True)
class NewsFeature:
    story_id: str
    cluster_id: str
    normalized_language: str
    event_class: str
    sentiment: float
    confidence: float
    evidence_hash: str
    source_ids: tuple[str, ...]
    trade_action: str = "NO_TRADE"
    can_send_order: bool = False


@dataclass
class NewsSafetyLayer:
    trusted_sources: frozenset[str]
    max_age: timedelta = timedelta(hours=24)
    min_reliability: float = 0.60
    min_confidence: float = 0.65
    _versions: dict[str, int] = field(default_factory=dict, init=False)

    def ingest(self, rows: Iterable[NewsRecord], *, as_of: datetime) -> list[NewsRecord]:
        accepted: list[NewsRecord] = []
        seen_content: set[str] = set()
        for row in sorted(rows, key=lambda r: (r.publication_time, r.story_id, r.version)):
            if row.source_id not in self.trusted_sources:
                continue
            if row.publication_time > as_of or row.ingestion_time > as_of:
                continue
            if as_of - row.publication_time > self.max_age:
                continue
            if row.source_reliability < self.min_reliability:
                continue
            expected = self._versions.get(row.story_id, 0) + 1
            if row.version != expected:
                continue
            digest = sha256(" ".join(row.text.lower().split()).encode()).hexdigest()
            if digest in seen_content:
                continue
            seen_content.add(digest)
            self._versions[row.story_id] = row.version
            accepted.append(row)
        return accepted

    @staticmethod
    def classify(rows: Iterable[NewsRecord], llm_result: Mapping[str, object]) -> NewsFeature:
        rows = list(rows)
        if not rows:
            raise ValueError("source evidence required")
        # LLM output is DATA only: fixed schema, bounded values, no commands/tools/order fields.
        allowed = {"event_class", "sentiment", "confidence", "language"}
        if set(llm_result) - allowed:
            raise ValueError("schema-invalid LLM result")
        event_class = str(llm_result.get("event_class", "UNKNOWN"))[:64]
        sentiment = max(-1.0, min(1.0, float(llm_result.get("sentiment", 0.0))))
        confidence = max(0.0, min(1.0, float(llm_result.get("confidence", 0.0))))
        language = str(llm_result.get("language", "und")).lower()[:16]
        evidence = "|".join(f"{r.source_id}:{r.story_id}:{r.version}:{r.source_url}" for r in rows)
        cluster_id = sha256("|".join(sorted(r.story_id for r in rows)).encode()).hexdigest()[:24]
        return NewsFeature(
            story_id=rows[-1].story_id,
            cluster_id=cluster_id,
            normalized_language=language,
            event_class=event_class,
            sentiment=sentiment,
            confidence=confidence,
            evidence_hash=sha256(evidence.encode()).hexdigest(),
            source_ids=tuple(sorted({r.source_id for r in rows})),
            trade_action="NO_TRADE",
            can_send_order=False,
        )

    def deterministic_risk_gate(self, feature: NewsFeature, *, conflicting_sources: bool = False) -> str:
        if conflicting_sources or feature.confidence < self.min_confidence or len(feature.source_ids) < 1:
            return "NO_TRADE"
        return "FEATURE_ONLY"
