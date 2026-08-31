from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class AvailabilityTier(str, Enum):
    SINGLE_HOST = "SINGLE_HOST"
    HA_STANDBY = "HA_STANDBY"


@dataclass(frozen=True)
class AvailabilityProfile:
    tier: AvailabilityTier
    external_backup: bool
    restart_reconciliation: bool
    host_failure_downtime_disclosed: bool
    database_ha_or_tested_replication: bool = False
    redis_failover_or_persistence: bool = False
    standby_trading_engine: bool = False
    external_watchdog: bool = False
    deterministic_failover_reconciliation: bool = False

    def validate(self) -> None:
        if not self.external_backup or not self.restart_reconciliation:
            raise ValueError("external backup and restart reconciliation are mandatory")
        if self.tier is AvailabilityTier.SINGLE_HOST:
            if not self.host_failure_downtime_disclosed:
                raise ValueError("single-host downtime must be disclosed")
            return
        required = {
            "database_ha_or_tested_replication": self.database_ha_or_tested_replication,
            "redis_failover_or_persistence": self.redis_failover_or_persistence,
            "standby_trading_engine": self.standby_trading_engine,
            "external_watchdog": self.external_watchdog,
            "deterministic_failover_reconciliation": self.deterministic_failover_reconciliation,
        }
        missing = [k for k, ok in required.items() if not ok]
        if missing:
            raise ValueError("HA profile incomplete: " + ",".join(missing))


@dataclass(frozen=True)
class FailoverEvidence:
    active_process_kill_passed: bool
    stale_leader_fencing_passed: bool
    private_stream_reconciliation_passed: bool
    host_loss_simulation_passed: bool = False
    db_failover_passed: bool = False
    redis_failover_passed: bool = False
    network_partition_passed: bool = False

    def assert_ha_drill_complete(self) -> None:
        missing = [name for name, value in self.__dict__.items() if not value]
        if missing:
            raise ValueError("HA drill incomplete: " + ",".join(missing))
