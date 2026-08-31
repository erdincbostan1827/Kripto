from __future__ import annotations
from dataclasses import dataclass
from typing import Mapping

@dataclass(frozen=True)
class ApiSchema:
    version:str
    required_fields:frozenset[str]
    optional_fields:frozenset[str]=frozenset()

@dataclass(frozen=True)
class SchemaCompatibility:
    compatible:bool
    missing_required:tuple[str,...]
    unknown_fields:tuple[str,...]
    version:str

def validate_payload(payload:Mapping[str,object], schema:ApiSchema, *, reject_unknown=False)->SchemaCompatibility:
    keys=set(payload); missing=sorted(schema.required_fields-keys); known=schema.required_fields|schema.optional_fields
    unknown=sorted(keys-known)
    return SchemaCompatibility(not missing and (not reject_unknown or not unknown),tuple(missing),tuple(unknown),schema.version)

def changelog_requires_review(old:ApiSchema,new:ApiSchema)->bool:
    return bool(new.required_fields-old.required_fields or old.required_fields-new.required_fields)
