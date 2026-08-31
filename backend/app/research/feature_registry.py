from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping, Sequence
import math


@dataclass(frozen=True)
class FeatureSpec:
    name: str
    version: str
    formula: str
    required_inputs: tuple[str, ...]
    warmup: int
    timeframe: str
    latency_ms: int
    availability_semantics: str
    expected_range: tuple[float, float]
    missing_value_policy: str
    directionality_assumption: str | None = None

    def __post_init__(self) -> None:
        if not self.name or not self.version or not self.formula or not self.required_inputs:
            raise ValueError("feature contract incomplete")
        if self.warmup < 0 or self.latency_ms < 0:
            raise ValueError("negative warmup/latency")
        if self.expected_range[0] >= self.expected_range[1]:
            raise ValueError("invalid expected range")


@dataclass
class FeatureRegistry:
    _features: dict[tuple[str, str], FeatureSpec] = field(default_factory=dict)

    def register(self, spec: FeatureSpec) -> None:
        key = (spec.name, spec.version)
        if key in self._features:
            raise ValueError("feature version already registered")
        self._features[key] = spec

    def get(self, name: str, version: str) -> FeatureSpec:
        return self._features[(name, version)]


def correlation_matrix(series: Mapping[str, Sequence[float]]) -> dict[str, dict[str, float]]:
    names = sorted(series)
    result: dict[str, dict[str, float]] = {n: {} for n in names}
    for a in names:
        for b in names:
            xa, xb = list(series[a]), list(series[b])
            if len(xa) != len(xb) or len(xa) < 2:
                raise ValueError("aligned observations required")
            ma, mb = sum(xa) / len(xa), sum(xb) / len(xb)
            num = sum((x-ma)*(y-mb) for x,y in zip(xa,xb))
            da = math.sqrt(sum((x-ma)**2 for x in xa)); db = math.sqrt(sum((y-mb)**2 for y in xb))
            result[a][b] = 0.0 if da == 0 or db == 0 else num/(da*db)
    return result


def cluster_redundant(corr: Mapping[str, Mapping[str, float]], threshold: float = 0.90) -> tuple[tuple[str, ...], ...]:
    remaining = set(corr); clusters=[]
    while remaining:
        root=min(remaining); group={root}
        for other in sorted(remaining-{root}):
            if abs(float(corr[root][other])) >= threshold:
                group.add(other)
        remaining -= group; clusters.append(tuple(sorted(group)))
    return tuple(clusters)


@dataclass(frozen=True)
class AblationResult:
    baseline_oos: float
    incremental_oos: Mapping[str, float]
    regime_contribution: Mapping[str, Mapping[str, float]]
    importance_method: str | None = None

    def useful_features(self, min_increment: float = 0.0) -> tuple[str, ...]:
        return tuple(sorted(k for k,v in self.incremental_oos.items() if float(v) > min_increment))
