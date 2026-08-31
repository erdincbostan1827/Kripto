from __future__ import annotations

from dataclasses import dataclass
import json
import sqlite3
import time
from contextlib import closing
from pathlib import Path


@dataclass(frozen=True)
class EscalationState:
    alert_key: str
    severity: str
    first_seen_at: float
    last_seen_at: float
    next_escalation_at: float
    attempts: int
    acknowledged: bool
    resolved: bool


class PersistentEscalationLedger:
    """Restart-safe alert escalation state backed by a local SQLite journal."""

    def __init__(self, path: str | Path):
        self.path = str(path)
        self._init_schema()

    def _connect(self):
        db = sqlite3.connect(self.path, isolation_level=None)
        db.row_factory = sqlite3.Row
        return db

    def _init_schema(self) -> None:
        with closing(self._connect()) as db:
            db.execute(
                """
                CREATE TABLE IF NOT EXISTS alert_escalation (
                    alert_key TEXT PRIMARY KEY,
                    severity TEXT NOT NULL,
                    first_seen_at REAL NOT NULL,
                    last_seen_at REAL NOT NULL,
                    next_escalation_at REAL NOT NULL,
                    attempts INTEGER NOT NULL,
                    acknowledged INTEGER NOT NULL,
                    resolved INTEGER NOT NULL,
                    evidence_json TEXT NOT NULL
                )
                """
            )

    def record(self, alert_key: str, severity: str, *, now: float | None = None, escalation_seconds: float = 300.0, evidence: dict | None = None) -> EscalationState:
        if escalation_seconds <= 0:
            raise ValueError("escalation_seconds must be positive")
        now = time.time() if now is None else float(now)
        evidence_json = json.dumps(evidence or {}, sort_keys=True, separators=(",", ":"))
        with closing(self._connect()) as db:
            row = db.execute("SELECT * FROM alert_escalation WHERE alert_key=?", (alert_key,)).fetchone()
            if row is None or bool(row["resolved"]):
                db.execute(
                    "INSERT OR REPLACE INTO alert_escalation VALUES (?,?,?,?,?,?,?,?,?)",
                    (alert_key, severity, now, now, now + escalation_seconds, 0, 0, 0, evidence_json),
                )
            else:
                db.execute(
                    "UPDATE alert_escalation SET severity=?, last_seen_at=?, evidence_json=? WHERE alert_key=?",
                    (severity, now, evidence_json, alert_key),
                )
        return self.get(alert_key)

    def due(self, *, now: float | None = None) -> list[EscalationState]:
        now = time.time() if now is None else float(now)
        with closing(self._connect()) as db:
            rows = db.execute(
                "SELECT * FROM alert_escalation WHERE resolved=0 AND acknowledged=0 AND next_escalation_at<=? ORDER BY next_escalation_at, alert_key",
                (now,),
            ).fetchall()
        return [self._row(row) for row in rows]

    def mark_escalated(self, alert_key: str, *, now: float, escalation_seconds: float) -> EscalationState:
        if escalation_seconds <= 0:
            raise ValueError("escalation_seconds must be positive")
        with closing(self._connect()) as db:
            cur = db.execute(
                "UPDATE alert_escalation SET attempts=attempts+1, last_seen_at=?, next_escalation_at=? WHERE alert_key=? AND resolved=0 AND acknowledged=0",
                (float(now), float(now) + escalation_seconds, alert_key),
            )
            if cur.rowcount != 1:
                raise LookupError("active unacknowledged alert not found")
        return self.get(alert_key)

    def acknowledge(self, alert_key: str) -> EscalationState:
        with closing(self._connect()) as db:
            cur = db.execute("UPDATE alert_escalation SET acknowledged=1 WHERE alert_key=? AND resolved=0", (alert_key,))
            if cur.rowcount != 1:
                raise LookupError("active alert not found")
        return self.get(alert_key)

    def resolve(self, alert_key: str) -> EscalationState:
        with closing(self._connect()) as db:
            cur = db.execute("UPDATE alert_escalation SET resolved=1 WHERE alert_key=?", (alert_key,))
            if cur.rowcount != 1:
                raise LookupError("alert not found")
        return self.get(alert_key)

    def get(self, alert_key: str) -> EscalationState:
        with closing(self._connect()) as db:
            row = db.execute("SELECT * FROM alert_escalation WHERE alert_key=?", (alert_key,)).fetchone()
        if row is None:
            raise LookupError(alert_key)
        return self._row(row)

    @staticmethod
    def _row(row: sqlite3.Row) -> EscalationState:
        return EscalationState(
            alert_key=row["alert_key"], severity=row["severity"], first_seen_at=row["first_seen_at"],
            last_seen_at=row["last_seen_at"], next_escalation_at=row["next_escalation_at"], attempts=row["attempts"],
            acknowledged=bool(row["acknowledged"]), resolved=bool(row["resolved"]),
        )
