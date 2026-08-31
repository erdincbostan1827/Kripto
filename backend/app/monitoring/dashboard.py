from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class DashboardSnapshot:
    timestamp: str
    mode: str
    exchange_status: str
    data_status: str
    data_age_seconds: float | None
    engine_status: str
    risk_status: str
    system_safe: bool
    user_message: str
    top_candidates: tuple[dict[str, Any], ...]
    open_positions: int
    open_orders: int
    critical_alerts: int
    portfolio_exposure: float | None
    daily_pnl: float | None
    drawdown: float | None
    source: str
    selected_symbol: str | None
    selected_price: float | None
    recent_signals: tuple[dict[str, Any], ...]
    protection_status: str
    protection_message: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_dashboard_snapshot(
    *,
    mode: str,
    health: dict[str, Any],
    scanner: dict[str, Any],
    portfolio: dict[str, Any],
    risk_state: str,
    critical_alerts: int = 0,
    daily_pnl: float | None = None,
    drawdown: float | None = None,
    portfolio_exposure: float | None = None,
    selected_market: dict[str, Any] | None = None,
    recent_signals: list[dict[str, Any]] | None = None,
    protection_confirmed: bool = False,
) -> DashboardSnapshot:
    components = health.get("components", {}) if isinstance(health, dict) else {}
    exchange = components.get("exchange", {}) if isinstance(components, dict) else {}
    data = components.get("data_freshness", components.get("market_data", {})) if isinstance(components, dict) else {}
    engine = components.get("trading_engine", {}) if isinstance(components, dict) else {}

    ready = bool(health.get("ready_for_new_risk", False)) if isinstance(health, dict) else False
    exchange_ok = bool(exchange.get("ok", exchange.get("status") in {"PASS", "OK", "HEALTHY"})) if isinstance(exchange, dict) else False
    data_ok = bool(data.get("ok", data.get("status") in {"PASS", "OK", "HEALTHY"})) if isinstance(data, dict) else False
    engine_ok = bool(engine.get("ok", engine.get("status") in {"PASS", "OK", "HEALTHY"})) if isinstance(engine, dict) else False
    data_age = data.get("age_seconds") if isinstance(data, dict) else None

    risk_upper = str(risk_state).upper()
    safe = ready and risk_upper not in {"HALTED", "MANUAL_REVIEW_REQUIRED", "STOPPING"}
    if safe:
        message = "Sistem sağlıklı. Yeni risk yalnız tanımlı limitler içinde değerlendirilebilir."
    elif not data_ok:
        message = "Yeni işlemler durduruldu — piyasa verisi sağlıklı veya yeterince güncel değil."
    elif not exchange_ok:
        message = "Yeni işlemler durduruldu — exchange bağlantısı doğrulanamadı."
    else:
        message = "Yeni işlemler durduruldu — risk veya sistem sağlık kapısı geçilmedi."

    items = scanner.get("items", []) if isinstance(scanner, dict) else []
    top = tuple(dict(x) for x in items[:10] if isinstance(x, dict))
    return DashboardSnapshot(
        timestamp=datetime.now(timezone.utc).isoformat(),
        mode=str(mode),
        exchange_status="AKTİF" if exchange_ok else "SORUNLU",
        data_status="AKTİF" if data_ok else "GECİKMİŞ/BELİRSİZ",
        data_age_seconds=float(data_age) if isinstance(data_age, (int, float)) else None,
        engine_status="GÜVENLİ" if engine_ok else "KISITLI/BELİRSİZ",
        risk_status=str(risk_state),
        system_safe=safe,
        user_message=message,
        top_candidates=top,
        open_positions=int(portfolio.get("open_positions", 0)) if isinstance(portfolio, dict) else 0,
        open_orders=int(portfolio.get("open_orders", 0)) if isinstance(portfolio, dict) else 0,
        critical_alerts=max(0, int(critical_alerts)),
        portfolio_exposure=portfolio_exposure,
        daily_pnl=daily_pnl,
        drawdown=drawdown,
        source=str(portfolio.get("source", scanner.get("source", "UNKNOWN"))) if isinstance(portfolio, dict) else "UNKNOWN",
        selected_symbol=str(selected_market.get("symbol")) if isinstance(selected_market, dict) and selected_market.get("symbol") else None,
        selected_price=float(selected_market.get("ticker", {}).get("last_price", selected_market.get("ticker", {}).get("price"))) if isinstance(selected_market, dict) and isinstance(selected_market.get("ticker"), dict) and selected_market.get("ticker", {}).get("last_price", selected_market.get("ticker", {}).get("price")) is not None else None,
        recent_signals=tuple(dict(x) for x in (recent_signals or [])[:10] if isinstance(x, dict)),
        protection_status="CONFIRMED" if protection_confirmed else "UNVERIFIED",
        protection_message="Pozisyon korunuyor — exchange üzerindeki stop emri doğrulandı" if protection_confirmed else "Pozisyon koruması exchange üzerinde doğrulanmadı",
    )
