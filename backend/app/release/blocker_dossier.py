from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Iterable
import json
import yaml


EXTERNAL_SECTIONS = {43, 51, 96, 97, 99, 100, 178, 181, 184, 189}
SUPPLY_CHAIN_SECTIONS = {96, 97, 189}
RECOVERY_SECTIONS = {178, 184}
CAMPAIGN_SECTIONS = {43, 51, 100}


@dataclass(frozen=True)
class ExternalEvidence:
    key: str
    status: str
    environment: str
    evidence_path: str | None
    evidence_sha256: str | None
    real_system: bool
    exit_code: int | None
    observed_at: datetime

    def validate(self, root: Path) -> tuple[bool, str]:
        if self.status != "PASS":
            return False, f"{self.key}: status is not PASS"
        if not self.real_system:
            return False, f"{self.key}: mock/simulated evidence cannot satisfy external acceptance"
        if self.exit_code != 0:
            return False, f"{self.key}: successful exit code evidence required"
        if self.observed_at.tzinfo is None:
            return False, f"{self.key}: observed_at must be timezone-aware"
        if not self.evidence_path or not self.evidence_sha256:
            return False, f"{self.key}: evidence path and sha256 required"
        path = root / self.evidence_path
        if not path.is_file() or path.stat().st_size == 0:
            return False, f"{self.key}: evidence artifact missing or empty"
        digest = sha256(path.read_bytes()).hexdigest()
        if digest != self.evidence_sha256:
            return False, f"{self.key}: evidence checksum mismatch"
        return True, "PASS"


@dataclass(frozen=True)
class RequirementBlocker:
    requirement_id: str
    section: int
    description: str
    category: str
    external_required: bool


def classify_requirement(section: int, description: str) -> tuple[str, bool]:
    text = description.lower()
    if section in SUPPLY_CHAIN_SECTIONS or any(x in text for x in ("sbom", "sast", "trivy", "pip-audit", "signing", "git sha", "lock hash")):
        return "SUPPLY_CHAIN_PROVENANCE", True
    if section in RECOVERY_SECTIONS or any(x in text for x in ("pitr", "restore drill", "failover", "network partition", "host loss")):
        return "RECOVERY_HA_RUNTIME", True
    if section in CAMPAIGN_SECTIONS or any(x in text for x in ("testnet", "execution divergence", "takvim süresi", "piyasa rejimi")):
        return "MARKET_CAMPAIGN", True
    if section == 42 and text.strip() == "redis":
        return "RUNTIME_INTEGRATION", True
    if section == 46:
        return "CONTAINER_RUNTIME", True
    # Section 99 is the canonical advanced fault-injection/restart-drill section.
    # Umbrella requirements in that section must remain externally blocked until
    # their real Redis/PostgreSQL/process restart evidence exists; classifying
    # them as local/ambiguous creates a contradictory operator plan.
    if section == 99:
        return "RUNTIME_FAULT_DRILL", True
    if section == 181 and "worm" in text:
        return "EXTERNAL_IMMUTABLE_STORAGE", True
    return "LOCAL_OR_AMBIGUOUS", section in EXTERNAL_SECTIONS


def build_requirement_blockers(matrix_path: Path, *, matrix_doc: dict | None = None) -> tuple[RequirementBlocker, ...]:
    doc = matrix_doc if matrix_doc is not None else yaml.safe_load(matrix_path.read_text(encoding="utf-8"))
    blockers: list[RequirementBlocker] = []
    for row in doc.get("requirements", []):
        if row.get("priority") != "P0" or row.get("status") == "PASS":
            continue
        category, external = classify_requirement(int(row["section"]), str(row.get("description", "")))
        blockers.append(
            RequirementBlocker(
                requirement_id=str(row["requirement_id"]),
                section=int(row["section"]),
                description=str(row.get("description", "")),
                category=category,
                external_required=external,
            )
        )
    return tuple(blockers)


def render_blocker_dossier(matrix_path: Path, output_path: Path) -> dict:
    blockers = build_requirement_blockers(matrix_path)
    by_category: dict[str, int] = {}
    for blocker in blockers:
        by_category[blocker.category] = by_category.get(blocker.category, 0) + 1
    payload = {
        "schema_version": "1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "p0_blocker_count": len(blockers),
        "external_required_count": sum(1 for b in blockers if b.external_required),
        "by_category": dict(sorted(by_category.items())),
        "blockers": [b.__dict__ for b in blockers],
        "truth_policy": "External acceptance is PASS only with real-system, exit-code-0, checksum-verified evidence; mock/simulated evidence remains blocked.",
    }
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload
