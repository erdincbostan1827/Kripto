from __future__ import annotations
from dataclasses import dataclass
from typing import Callable

class EventSchemaError(RuntimeError):
    """Event schema contract violation."""
class EventMigrationRequired(EventSchemaError):
    """Explicit event migration is required before replay."""

@dataclass(frozen=True)
class EventSchema:
    event_type: str
    version: int
    required_fields: frozenset[str]
    optional_fields: frozenset[str] = frozenset()

class EventSchemaRegistry:
    """Fail-closed registry for persisted/event-bus semantic contracts."""
    def __init__(self):
        self._schemas: dict[tuple[str,int], EventSchema] = {}
        self._upcasters: dict[tuple[str,int], Callable[[dict], dict]] = {}

    def register(self, schema: EventSchema) -> None:
        key=(schema.event_type, schema.version)
        if schema.version < 1 or not schema.required_fields.isdisjoint(schema.optional_fields):
            raise ValueError('invalid event schema')
        old=self._schemas.get(key)
        if old and old != schema: raise EventSchemaError('schema version already registered with different semantics')
        self._schemas[key]=schema

    def register_upcaster(self,event_type:str,from_version:int,fn:Callable[[dict],dict])->None:
        if (event_type,from_version) in self._upcasters: raise EventSchemaError('duplicate upcaster')
        self._upcasters[(event_type,from_version)]=fn

    def validate(self,event_type:str,version:int,payload:dict)->dict:
        schema=self._schemas.get((event_type,version))
        if schema is None: raise EventMigrationRequired(f'unknown schema {event_type}@{version}')
        missing=schema.required_fields-set(payload)
        if missing: raise EventSchemaError(f'missing required fields: {sorted(missing)}')
        # Unknown fields are tolerated for forward-compatible additive changes.
        return dict(payload)

    def migrate_to_latest(self,event_type:str,version:int,payload:dict)->tuple[int,dict]:
        cur_v,cur=version,dict(payload)
        while (event_type,cur_v) in self._upcasters:
            cur=self._upcasters[(event_type,cur_v)](cur); cur_v+=1
        self.validate(event_type,cur_v,cur)
        return cur_v,cur
