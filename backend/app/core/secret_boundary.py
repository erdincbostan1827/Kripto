from __future__ import annotations
from dataclasses import dataclass
import os
import re

_SECRET_NAME = re.compile(r'(SECRET|TOKEN|PASSWORD|API[_-]?KEY|PRIVATE[_-]?KEY|CREDENTIAL)', re.I)


def mask_secret(value: str | None) -> str:
    if not value:
        return ''
    value = str(value)
    if len(value) <= 4:
        return '*' * len(value)
    return value[:2] + ('*' * max(4, len(value)-4)) + value[-2:]


def redact_mapping(values: dict) -> dict:
    out = {}
    for key, value in values.items():
        out[key] = mask_secret(str(value)) if _SECRET_NAME.search(str(key)) else value
    return out


@dataclass(frozen=True)
class SecretBootstrapCheck:
    valid: bool
    errors: tuple[str, ...]


def validate_secret_bootstrap(env: dict[str,str] | None=None, *, production: bool=False) -> SecretBootstrapCheck:
    env = dict(os.environ if env is None else env)
    errors=[]
    if production:
        if not env.get('APP_SECRET_KEY'):
            errors.append('APP_SECRET_KEY_REQUIRED')
        if env.get('ALLOW_MOCK','0').strip().lower() in {'1','true','yes','on'}:
            errors.append('MOCK_FORBIDDEN_IN_PRODUCTION')
        for key, value in env.items():
            if _SECRET_NAME.search(key) and value and value.lower() in {'changeme','change-me','secret','password','test'}:
                errors.append(f'INSECURE_DEFAULT:{key}')
    return SecretBootstrapCheck(not errors, tuple(sorted(errors)))
