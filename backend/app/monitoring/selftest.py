from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import shutil

from app.monitoring.health import HealthService


@dataclass(frozen=True)
class CheckResult:
    name: str
    status: str
    required: bool
    detail: str | None = None

    @property
    def ok(self) -> bool:
        return self.status in {"PASS", "UP", "MOCK_UP"}


class SelfTestService:
    """Operator-facing preflight aggregator.

    It never converts an unavailable production dependency into PASS. External
    integrations can be injected as callables returning truthy/falsey values.
    """

    def __init__(
        self,
        health: HealthService,
        *,
        environment_check=None,
        credential_check=None,
        permission_check=None,
        telegram_check=None,
        websocket_check=None,
        risk_config_check=None,
        strategy_config_check=None,
        docker_check=None,
        memory_check=None,
        disk_path: str = ".",
        min_free_disk_bytes: int = 512 * 1024 * 1024,
    ):
        self.health = health
        self.environment_check = environment_check
        self.credential_check = credential_check
        self.permission_check = permission_check
        self.telegram_check = telegram_check
        self.websocket_check = websocket_check
        self.risk_config_check = risk_config_check
        self.strategy_config_check = strategy_config_check
        self.docker_check = docker_check
        self.memory_check = memory_check
        self.disk_path = disk_path
        self.min_free_disk_bytes = int(min_free_disk_bytes)

    @staticmethod
    def _call(name: str, fn, required: bool = True) -> CheckResult:
        if fn is None:
            return CheckResult(name, "UNCONFIGURED", required, "check not configured")
        try:
            value = fn()
            if isinstance(value, tuple):
                ok, detail = bool(value[0]), str(value[1]) if len(value) > 1 else None
            else:
                ok, detail = bool(value), None
            return CheckResult(name, "PASS" if ok else "FAIL", required, detail)
        except Exception:
            return CheckResult(name, "FAIL", required, "check raised exception")

    def run(self) -> dict:
        health = self.health.snapshot()
        checks: list[CheckResult] = []
        for name in ("database", "redis", "exchange", "clock"):
            state = str(health.get(name, "UNCONFIGURED"))
            checks.append(CheckResult(name, "PASS" if state in {"UP", "MOCK_UP"} else "FAIL", True, state))

        checks.extend([
            self._call("environment", self.environment_check),
            self._call("api_credentials", self.credential_check),
            self._call("exchange_permissions", self.permission_check),
            self._call("telegram", self.telegram_check),
            self._call("websocket", self.websocket_check),
            self._call("risk_configuration", self.risk_config_check),
            self._call("strategy_configuration", self.strategy_config_check),
            self._call("memory", self.memory_check),
            self._call("docker_services", self.docker_check),
        ])
        try:
            free = shutil.disk_usage(self.disk_path).free
            checks.append(CheckResult("disk_space", "PASS" if free >= self.min_free_disk_bytes else "FAIL", True, f"free_bytes={free}"))
        except Exception:
            checks.append(CheckResult("disk_space", "FAIL", True, "disk probe failed"))

        required = [x for x in checks if x.required]
        ok = all(x.ok for x in required)
        return {
            "status": "PASS" if ok else "FAIL",
            "ready_for_new_risk": ok,
            "checked_at": datetime.now(timezone.utc).isoformat(),
            "checks": [x.__dict__ for x in checks],
            "failures": [x.name for x in required if not x.ok],
        }
