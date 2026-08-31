from pathlib import Path
import json

ROOT=Path(__file__).resolve().parents[2]

def text(path:str)->str:
    return (ROOT/path).read_text(encoding='utf-8')

def test_phase130_official_tauri_reference_is_version_checked_without_claiming_lock_or_build():
    doc=text('docs/TECHNOLOGY_VERSION_VERIFICATION.md')
    cargo=text('frontend/src-tauri/Cargo.toml')
    assert '2026-08-29' in doc
    assert 'Tauri core: `2.11.5`' in doc and 'tauri-build`: `2.6.3`' in doc
    assert 'tauri = "=2.11.5"' in cargo and 'tauri-build = "=2.6.3"' in cargo
    assert 'lockfile is required before production dependency acceptance' in doc
    assert 'build NOT_TESTED' in doc
    assert not (ROOT/'frontend/src-tauri/Cargo.lock').exists()

def test_phase130_optional_tauri_shell_packages_react_but_keeps_trading_server_side_and_minimal_capabilities():
    conf=json.loads(text('frontend/src-tauri/tauri.conf.json'))
    main=text('frontend/src-tauri/src/main.rs')
    cap=json.loads(text('frontend/src-tauri/capabilities/default.json'))
    assert conf['build']['beforeBuildCommand']=='npm run build'
    assert conf['build']['frontendDist']=='../dist'
    assert conf['app']['security']['csp']
    assert cap['permissions']==['core:default','notification:default']
    assert 'Trading/execution/risk engines intentionally remain server-side' in main
    forbidden=('api_secret','secret_key','withdraw','Command::new','shell:','fs:','process:')
    combined=(main+text('frontend/src-tauri/tauri.conf.json')+text('frontend/src-tauri/capabilities/default.json')).lower()
    assert all(token.lower() not in combined for token in forbidden)

def test_phase130_desktop_api_boundary_requires_https_no_url_credentials_and_wss():
    runtime=text('frontend/src/runtime/clientShell.ts')
    client=text('frontend/src/api/client.ts')
    realtime=text('frontend/src/realtime/serverState.ts')
    assert 'TAURI_REQUIRES_HTTPS_BACKEND' in runtime
    assert 'API_BASE_URL_MUST_NOT_CONTAIN_CREDENTIALS' in runtime
    assert "u.protocol=u.protocol==='https:'?'wss:':'ws:'" in runtime
    assert "fetch(apiUrl(path)" in client
    assert "new WebSocket(websocketUrl('/api/v1/ws'))" in realtime

def test_phase130_client_server_compatibility_is_fail_closed_for_high_risk_ui_boot():
    runtime=text('frontend/src/runtime/clientShell.ts')
    main=text('frontend/src/main.tsx')
    auth=text('frontend/src/components/AuthGate.tsx')
    assert 'isClientCompatible' in runtime and "c.api_version!=='v1'" in runtime
    assert 'min_client' in runtime and 'max_client' in runtime
    assert 'if(!isClientCompatible(c))throw new Error' in main
    assert 'if(!isClientCompatible(c)){setState' in auth
    assert 'Risk artırıcı işlemler bloklandı' in auth

def test_phase130_desktop_shell_has_no_execution_ownership_and_cannot_grant_withdrawal_by_client_compromise():
    doc=text('docs/TECHNOLOGY_VERSION_VERIFICATION.md').lower()
    settings=text('frontend/src/pages/Settings.tsx').lower()
    assert 'execution-engine ownership' in doc
    assert 'closed desktop client therefore cannot stop server-side open-position management' in doc
    assert 'withdrawals' in doc
    assert 'secret değerleri wizard state’ine yazılmaz' in settings


def test_phase133_tauri_native_notification_is_opt_in_without_broad_client_permissions():
    cargo=text('frontend/src-tauri/Cargo.toml')
    main=text('frontend/src-tauri/src/main.rs')
    cap=json.loads(text('frontend/src-tauri/capabilities/default.json'))
    assert 'tauri-plugin-notification = "=2.3.3"' in cargo
    assert '.plugin(tauri_plugin_notification::init())' in main
    assert cap['permissions']==['core:default','notification:default']
    assert all(not p.startswith(('fs:','shell:','process:')) for p in cap['permissions'])
