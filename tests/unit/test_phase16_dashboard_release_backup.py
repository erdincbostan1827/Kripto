from pathlib import Path

from app.monitoring.dashboard import build_dashboard_snapshot
from scripts.generate_local_sbom import generate

ROOT=Path(__file__).resolve().parents[2]


def test_dashboard_snapshot_is_user_facing_and_fail_closed():
    health={"ready_for_new_risk":False,"components":{"exchange":{"ok":True},"data_freshness":{"ok":False,"age_seconds":12.5},"trading_engine":{"ok":True}}}
    snap=build_dashboard_snapshot(mode="PAPER",health=health,scanner={"source":"MOCK","items":[{"symbol":"BTCUSDT","score":80}]},portfolio={"source":"MOCK","open_positions":2,"open_orders":3},risk_state="DEGRADED",critical_alerts=1,selected_market={"symbol":"BTCUSDT","ticker":{"last_price":123.45}},recent_signals=[{"symbol":"BTCUSDT","signal":"WATCH"}])
    assert not snap.system_safe
    assert snap.mode=="PAPER"
    assert snap.data_status=="GECİKMİŞ/BELİRSİZ"
    assert "Yeni işlemler durduruldu" in snap.user_message
    assert snap.open_positions==2 and snap.open_orders==3 and snap.critical_alerts==1
    assert snap.top_candidates[0]["symbol"]=="BTCUSDT"
    assert snap.selected_symbol=="BTCUSDT" and snap.selected_price==123.45
    assert snap.recent_signals[0]["signal"]=="WATCH"


def test_dashboard_snapshot_can_be_safe_only_when_health_and_risk_allow_it():
    health={"ready_for_new_risk":True,"components":{"exchange":{"ok":True},"data_freshness":{"ok":True,"age_seconds":0.4},"trading_engine":{"ok":True}}}
    snap=build_dashboard_snapshot(mode="PAPER",health=health,scanner={"items":[]},portfolio={},risk_state="NORMAL")
    assert snap.system_safe
    assert snap.exchange_status=="AKTİF" and snap.data_status=="AKTİF" and snap.engine_status=="GÜVENLİ"


def test_local_sbom_is_explicitly_unresolved_and_never_claims_supply_chain_acceptance():
    doc=generate(ROOT)
    assert doc["components"]
    meta=doc["metadata"]
    assert meta["resolved_dependency_lock"] is False
    assert meta["vulnerability_scan_performed"] is False
    assert "NOT_SUPPLY_CHAIN_ACCEPTANCE" in meta["classification"]
    assert all(c["resolved"] is False for c in doc["components"])


def test_backup_restore_scripts_are_encrypted_integrity_checked_and_fail_fast():
    backup=(ROOT/"scripts/backup.sh").read_text(encoding="utf-8")
    restore=(ROOT/"scripts/restore.sh").read_text(encoding="utf-8")
    assert "set -euo pipefail" in backup and "set -euo pipefail" in restore
    assert "pg_dump" in backup and "backup_crypto.py encrypt" in backup
    assert "sha256sum" in backup and "chmod 600" in backup
    assert "sha256sum -c" in restore and "backup_crypto.py decrypt" in restore and "pg_restore --exit-on-error" in restore
    assert "trading_restore" in restore


def test_dashboard_frontend_contract_contains_required_user_facing_sections():
    dash=(ROOT/"frontend/src/pages/Dashboard.tsx").read_text(encoding="utf-8")
    status=(ROOT/"frontend/src/components/StatusStrip.tsx").read_text(encoding="utf-8")
    required=["Portföy","Günlük P&L","Açık Risk","Drawdown","Pozisyon","Kritik Uyarı","En İyi Fırsatlar","Sinyal","Rejim"]
    for term in required: assert term in dash
    for term in ["PAPER","Exchange","Market Data","Engine","Risk"]: assert term in status
    assert "LIVE varsayılan olarak kapalıdır" in status


def test_grafana_dashboard_is_provisioned_with_real_health_panels():
    import json
    doc=json.loads((ROOT/"docker/grafana/dashboards/system-health.json").read_text(encoding="utf-8"))
    assert doc["uid"]=="ctp-health" and len(doc["panels"])>=5
    exprs=" ".join(t["expr"] for p in doc["panels"] for t in p.get("targets",[]))
    assert 'up{job="trading-app"}' in exprs
    assert "process_resident_memory_bytes" in exprs and "process_cpu_seconds_total" in exprs


def test_readme_contains_first_run_exchange_telegram_environment_and_error_guidance():
    text=(ROOT/"README.md").read_text(encoding="utf-8")
    for term in ["Binance API anahtarı","READ","Withdrawal","Telegram bot","BotFather","Environment variables","ilk kurulum sihirbazı","PAPER","Mobil / PWA / masaüstü","Kullanıcı dostu hata / uyarı sözlüğü","MANUAL_REVIEW_REQUIRED","UNPROTECTED_POSITION","UNKNOWN order"]:
        assert term in text


def test_ci_workflow_is_fail_closed_and_covers_backend_frontend_docker_and_release_gate():
    import yaml
    doc=yaml.safe_load((ROOT/".github/workflows/ci.yml").read_text(encoding="utf-8"))
    jobs=doc["jobs"]
    assert {"backend","frontend","docker","release-gate"} <= set(jobs)
    backend=" ".join(str(s.get("run","")) for s in jobs["backend"]["steps"])
    for term in ["compileall","ruff check","mypy","pytest","prohibited_scan.py","secret_scan.py","alembic upgrade head --sql","pip-audit"]:
        assert term in backend
    frontend=" ".join(str(s.get("run","")) for s in jobs["frontend"]["steps"])
    assert "frontend/package-lock.json" in frontend and "npm ci" in frontend and "npm test" in frontend and "npm run build" in frontend
    docker=" ".join(str(s.get("run","")) for s in jobs["docker"]["steps"])
    assert "docker compose" in docker and "build" in docker
    assert set(jobs["release-gate"]["needs"])=={"backend","frontend","docker"}
    assert any("release_gate.py" in str(s.get("run","")) for s in jobs["release-gate"]["steps"])


def test_third_party_notices_exists_and_docker_build_base_images_are_digest_pinned():
    notices=(ROOT/"THIRD_PARTY_NOTICES.md").read_text(encoding="utf-8")
    assert len(notices.strip())>40
    dockerfiles=[ROOT/"backend/Dockerfile",ROOT/"frontend/Dockerfile"]
    for path in dockerfiles:
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.startswith("FROM ") and " AS " not in line.upper() or line.startswith("FROM "):
                image=line.split()[1]
                if image.lower() in {"base","build"}: continue
                assert "@sha256:" in image


def test_dashboard_never_claims_position_protection_without_exchange_confirmation():
    h={"ready_for_new_risk":True,"components":{"exchange":{"ok":True},"data_freshness":{"ok":True},"trading_engine":{"ok":True}}}
    unknown=build_dashboard_snapshot(mode="PAPER",health=h,scanner={"items":[]},portfolio={},risk_state="NORMAL")
    assert unknown.protection_status=="UNVERIFIED" and "doğrulanmadı" in unknown.protection_message
    confirmed=build_dashboard_snapshot(mode="PAPER",health=h,scanner={"items":[]},portfolio={},risk_state="NORMAL",protection_confirmed=True)
    assert confirmed.protection_status=="CONFIRMED"
    assert confirmed.protection_message=="Pozisyon korunuyor — exchange üzerindeki stop emri doğrulandı"


def test_multi_asset_operator_ui_exposes_required_primary_areas_without_trade_all_control():
    app=(ROOT/"frontend/src/App.tsx").read_text(encoding="utf-8")
    i18n=(ROOT/"frontend/src/i18n/tr.ts").read_text(encoding="utf-8")
    joined="\n".join((ROOT/f"frontend/src/pages/{name}.tsx").read_text(encoding="utf-8") for name in ["Dashboard","Scanner","Analysis","Orders","Alerts","Research","Performance","Settings"])
    for term in ["Ana Ekran","Piyasa / Scanner","Analiz","Pozisyonlar & Emirler","Alarmlar","Backtest & Araştırma","Performans & Risk","Ayarlar / Sistem"]:
        assert term in app+i18n
    for term in ["correlation/concentration","Strategy","Data","Exchange","Backtest","Risk"]:
        assert term.lower() in joined.lower()
    assert "trade all" not in (app+joined).lower()


def test_ci_pytest_contract_includes_no_lookahead_and_recursive_indicator_guards():
    workflow=(ROOT/".github/workflows/ci.yml").read_text(encoding="utf-8")
    assert "pytest -q -W error" in workflow
    backtest=(ROOT/"tests/unit/test_backtest.py").read_text(encoding="utf-8")
    stability=(ROOT/"tests/unit/test_phase11_indicator_stability.py").read_text(encoding="utf-8")
    assert "test_next_bar_entry_and_costs" in backtest
    assert "test_recursive_indicator_stability_with_sufficient_warmup" in stability


def test_release_packaging_contract_is_content_addressed_and_writes_checksum_file():
    script=(ROOT/"scripts/package_release.py").read_text(encoding="utf-8")
    for term in ["PACKAGE_MANIFEST.json","sha256_file","SHA256SUMS.txt","verification","mismatches","forbidden"]:
        assert term in script
    assert 'RELEASE_ID = "0.3.0-local-acceptance"' in script
