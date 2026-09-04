from __future__ import annotations

from hashlib import sha256
import json
from typing import Final

PROFILE_ORDER: Final[tuple[str, ...]] = (
    "locks", "runtime", "restart-drills", "supply-chain", "pitr", "ha", "worm", "testnet", "provenance", "campaigns",
)

PROFILE_TO_GROUPS: Final[dict[str, tuple[str, ...]]] = {
    "locks": ("dependency_locks_and_frontend_build",),
    "runtime": ("runtime",),
    "restart-drills": ("restart_drills",),
    "supply-chain": ("supply_chain",),
    "pitr": ("pitr",),
    "ha": ("ha",),
    "worm": ("worm",),
    "testnet": ("testnet",),
    "provenance": ("provenance",),
    "campaigns": ("private_stream", "paper_campaign", "live_shadow", "profitability"),
}

ACCEPTANCE_PLANS: Final[dict[str, tuple[tuple[str, tuple[str, ...], bool], ...]]] = {
    "locks": (
        ("source_lock_compliance", ("python", "scripts/verify_source_locks.py"), True),
        ("backend_lock", ("uv", "lock", "--locked"), True),
        ("frontend_lock", ("npm", "--prefix", "frontend", "ci", "--ignore-scripts"), True),
        ("frontend_build", ("npm", "--prefix", "frontend", "run", "build"), True),
    ),
    "runtime": (
        ("docker_compose_config", ("docker", "compose", "config", "--quiet"), True),
        ("docker_compose_up", ("docker", "compose", "up", "-d", "postgres", "redis"), True),
        ("postgres_migration", ("docker", "compose", "run", "--rm", "app", "python", "-m", "scripts.run_container_migrations"), True),
        ("redis_ping", ("docker", "compose", "exec", "-T", "redis", "redis-cli", "ping"), True),
        ("runtime_health", ("docker", "compose", "ps"), True),
    ),
    "restart-drills": (
        ("redis_restart", ("docker", "compose", "restart", "redis"), True),
        ("redis_restart_health", ("docker", "compose", "exec", "-T", "redis", "redis-cli", "ping"), True),
        ("postgres_restart", ("docker", "compose", "restart", "postgres"), True),
        ("postgres_restart_health", ("docker", "compose", "exec", "-T", "postgres", "pg_isready"), True),
        ("restart_semantic_evidence", ("python", "scripts/external/run_approved_drill.py", "restart-drills"), True),
    ),
    "supply-chain": (("transferred_supply_chain_verification", ("python", "scripts/external/verify_transferred_supply_chain.py"), True),),
    "pitr": (("pitr_drill", ("python", "scripts/external/run_approved_drill.py", "pitr"), True),),
    "ha": (("ha_drill", ("python", "scripts/external/run_approved_drill.py", "ha"), True),),
    "worm": (("worm_storage", ("python", "scripts/external/run_approved_drill.py", "worm"), True),),
    "testnet": ((
        "binance_testnet",
        (
            "docker", "compose", "run", "--rm",
            "-e", "BINANCE_TESTNET_API_KEY",
            "-e", "BINANCE_TESTNET_API_SECRET",
            "-e", "BINANCE_TESTNET_EXECUTE",
            "-e", "BINANCE_TESTNET_SYMBOL",
            "-e", "BINANCE_TESTNET_MAX_NOTIONAL",
            "-e", "BINANCE_TESTNET_PARTIAL_PRICE",
            "app", "python", "scripts/external/binance_testnet_acceptance_v2.py",
        ),
        True,
    ),),
    "provenance": (
        ("ci_provenance_capture", ("python", "scripts/external/provenance_capture.py"), True),
        ("artifact_sign_verify", ("python", "scripts/external/run_approved_drill.py", "provenance"), True),
    ),
    "campaigns": (
        ("private_stream_evidence", ("python", "scripts/external/campaign_evidence_acceptance.py", "private-stream"), True),
        ("paper_campaign_evidence", ("python", "scripts/external/campaign_evidence_acceptance.py", "paper"), True),
        ("live_shadow_evidence", ("python", "scripts/external/campaign_evidence_acceptance.py", "live-shadow"), True),
        ("profitability_evidence", ("python", "scripts/external/campaign_evidence_acceptance.py", "profitability"), True),
    ),
}

GROUP_KEYS: Final[dict[str, tuple[str, ...]]] = {
    "dependency_locks_and_frontend_build": ("backend_lock", "frontend_lock", "frontend_build"),
    "runtime": ("docker_compose_config", "docker_compose_up", "postgres_migration", "redis_ping", "runtime_health"),
    "restart_drills": ("redis_restart", "redis_restart_health", "postgres_restart", "postgres_restart_health", "restart_semantic_evidence"),
    "supply_chain": ("transferred_supply_chain_verification",),
    "pitr": ("pitr_drill",),
    "ha": ("ha_drill",),
    "worm": ("worm_storage",),
    "testnet": ("binance_testnet",),
    "provenance": ("ci_provenance_capture", "artifact_sign_verify"),
    "private_stream": ("private_stream_evidence",),
    "paper_campaign": ("paper_campaign_evidence",),
    "live_shadow": ("live_shadow_evidence",),
    "profitability": ("profitability_evidence",),
}

RUNNER_GROUP_KEYS: Final[dict[str, tuple[str, ...]]] = {
    **GROUP_KEYS,
    "dependency_locks_and_frontend_build": ("source_lock_compliance", "backend_lock", "frontend_lock", "frontend_build"),
}

DEFAULT_GROUP_TTL_HOURS: Final[dict[str, int]] = {
    "dependency_locks_and_frontend_build": 168,
    "runtime": 24,
    "restart_drills": 24,
    "supply_chain": 168,
    "pitr": 24,
    "ha": 24,
    "worm": 24,
    "testnet": 24,
    "provenance": 168,
    "private_stream": 24,
    "paper_campaign": 168,
    "live_shadow": 24,
    "profitability": 168,
}

SUPPLEMENTAL_COMMAND_ROWS: Final[tuple[str, ...]] = ("uv_lock_file", "npm_lock_file", "credential_guard")
ACCEPTANCE_CONTRACT_SCHEMA: Final[str] = "1.1"


def build_plan(profile: str) -> list[tuple[str, list[str], bool]]:
    if profile == "all":
        rows = [row for name in PROFILE_ORDER for row in ACCEPTANCE_PLANS[name]]
    else:
        rows = list(ACCEPTANCE_PLANS[profile])
    return [(key, list(command), requires_real) for key, command, requires_real in rows]


def command_contract(profile: str) -> dict[str, list[str]]:
    rows = {key: list(command) for key, command, _ in build_plan(profile)}
    rows.update({key: [] for key in SUPPLEMENTAL_COMMAND_ROWS})
    return dict(sorted(rows.items()))


def command_contract_sha256(profile: str) -> str:
    raw = json.dumps(command_contract(profile), sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return sha256(raw).hexdigest()


def acceptance_contract_payload() -> dict[str, object]:
    return {
        "schema_version": ACCEPTANCE_CONTRACT_SCHEMA,
        "profile_order": list(PROFILE_ORDER),
        "profile_to_groups": {key: list(value) for key, value in PROFILE_TO_GROUPS.items()},
        "command_contract_sha256": {profile: command_contract_sha256(profile) for profile in (*PROFILE_ORDER, "all")},
        "group_keys": {key: list(value) for key, value in sorted(GROUP_KEYS.items())},
        "runner_group_keys": {key: list(value) for key, value in sorted(RUNNER_GROUP_KEYS.items())},
        "default_group_ttl_hours": dict(sorted(DEFAULT_GROUP_TTL_HOURS.items())),
        "supplemental_command_rows": list(SUPPLEMENTAL_COMMAND_ROWS),
    }


def acceptance_contract_sha256() -> str:
    raw = json.dumps(acceptance_contract_payload(), sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return sha256(raw).hexdigest()
