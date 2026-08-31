from __future__ import annotations

import json
import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from datetime import datetime, timezone
from typing import Any

SENSITIVE=("secret","password","token","api_key","authorization","cookie","credential")


def redact(value:Any,key:str|None=None)->Any:
    if key and any(marker in key.lower() for marker in SENSITIVE):
        return "[REDACTED]"
    if isinstance(value,dict):
        return {k:redact(v,str(k)) for k,v in value.items()}
    if isinstance(value,(list,tuple)):
        return [redact(v) for v in value]
    return value


class JsonFormatter(logging.Formatter):
    def format(self,record:logging.LogRecord)->str:
        payload={
            "timestamp":datetime.now(timezone.utc).isoformat().replace("+00:00","Z"),
            "level":record.levelname,
            "logger":record.name,
            "message":record.getMessage(),
        }
        for name in ("correlation_id","path","status_code","event_type","action"):
            if hasattr(record,name): payload[name]=getattr(record,name)
        if hasattr(record,"details"):
            payload["details"]=redact(getattr(record,"details"))
        if record.exc_info:
            payload["exception_type"]=record.exc_info[0].__name__ if record.exc_info[0] else "Exception"
        return json.dumps(redact(payload),ensure_ascii=False,separators=(",",":"),default=str)


def configure_json_logging(level:str="INFO", *, log_file:str|None=None, max_bytes:int=10_000_000, backup_count:int=5)->logging.Logger:
    logger=logging.getLogger("ctp")
    logger.setLevel(getattr(logging,level.upper(),logging.INFO))
    if not any(getattr(h,"_ctp_json",False) for h in logger.handlers):
        handler=logging.StreamHandler(sys.stderr); handler.setFormatter(JsonFormatter()); handler._ctp_json=True
        logger.addHandler(handler)
    if log_file and not any(getattr(h,"_ctp_rotating",False) for h in logger.handlers):
        path=Path(log_file); path.parent.mkdir(parents=True,exist_ok=True)
        rotating=RotatingFileHandler(path,maxBytes=max_bytes,backupCount=backup_count,encoding="utf-8")
        rotating.setFormatter(JsonFormatter()); rotating._ctp_rotating=True
        logger.addHandler(rotating)
    logger.propagate=False
    return logger
