from __future__ import annotations

import hashlib
import hmac
import json
from dataclasses import asdict, dataclass
from typing import Any

_PLACEHOLDERS = {"", "UNAVAILABLE", "UNKNOWN", "NOT_BUILT", "LOCAL-NOT-CI", "NOT_TESTED"}


@dataclass(frozen=True)
class ReleaseAttestation:
    release_id: str
    git_commit_sha: str
    source_tree_hash: str
    ci_run_id: str
    build_timestamp: str
    dependency_lock_hash: str | None
    sbom_hash: str | None
    container_digest: str | None
    frontend_artifact_hash: str | None
    migration_version: str
    architecture_profile_hash: str
    requirement_matrix_hash: str
    test_evidence_reference: str

    def canonical_bytes(self) -> bytes:
        return json.dumps(asdict(self), sort_keys=True, separators=(",", ":")).encode()

    def fingerprint(self) -> str:
        return hashlib.sha256(self.canonical_bytes()).hexdigest()

    def production_blockers(self) -> tuple[str, ...]:
        required = {
            "git_commit_sha": self.git_commit_sha,
            "ci_run_id": self.ci_run_id,
            "dependency_lock_hash": self.dependency_lock_hash,
            "sbom_hash": self.sbom_hash,
            "container_digest": self.container_digest,
            "frontend_artifact_hash": self.frontend_artifact_hash,
        }
        return tuple(name for name, value in required.items() if value is None or str(value).strip() in _PLACEHOLDERS)

    def assert_production_complete(self) -> None:
        blockers = self.production_blockers()
        if blockers:
            raise ValueError("incomplete release provenance: " + ",".join(blockers))


def sign_attestation(attestation: ReleaseAttestation, key: bytes) -> str:
    if len(key) < 32:
        raise ValueError("attestation signing key must be at least 256 bits")
    return hmac.new(key, attestation.canonical_bytes(), hashlib.sha256).hexdigest()


def verify_attestation(attestation: ReleaseAttestation, signature: str, key: bytes) -> bool:
    expected = sign_attestation(attestation, key)
    return hmac.compare_digest(expected, signature)
