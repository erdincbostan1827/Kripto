from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Callable, Any


@dataclass(frozen=True)
class ConfigMigrationResult:
    source_version: int
    target_version: int
    config: dict[str, Any]
    config_hash: str
    applied_migrations: tuple[str, ...]


class ConfigCompatibilityRegistry:
    def __init__(self, current_version: int):
        if current_version < 1:
            raise ValueError("current_version must be >= 1")
        self.current_version = current_version
        self._migrations: dict[int, tuple[int, str, Callable[[dict[str, Any]], dict[str, Any]]]] = {}

    def register(self, source_version: int, target_version: int, name: str, migration: Callable[[dict[str, Any]], dict[str, Any]]) -> None:
        if target_version != source_version + 1:
            raise ValueError("config migrations must be sequential")
        if source_version in self._migrations:
            raise ValueError("duplicate source version migration")
        self._migrations[source_version] = (target_version, name, migration)

    def migrate(self, raw: dict[str, Any]) -> ConfigMigrationResult:
        if "schema_version" not in raw:
            raise ValueError("schema_version is required")
        source = int(raw["schema_version"])
        if source > self.current_version:
            raise ValueError("future config schema is not supported")
        config = dict(raw)
        applied: list[str] = []
        version = source
        while version < self.current_version:
            step = self._migrations.get(version)
            if step is None:
                raise ValueError(f"missing config migration from version {version}")
            target, name, fn = step
            config = dict(fn(dict(config)))
            config["schema_version"] = target
            version = target
            applied.append(name)
        encoded = json.dumps(config, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        return ConfigMigrationResult(source, version, config, sha256(encoded).hexdigest(), tuple(applied))
