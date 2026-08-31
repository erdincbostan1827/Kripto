from pathlib import Path
import json
import shutil
import subprocess
import tempfile

from app.core.config import Settings
from app.core.enums import TradingMode
from app.paper.engine import PaperBroker

ROOT=Path(__file__).resolve().parents[2]


def test_phase134_paper_fixture_models_slippage_and_latency_without_real_orders():
    from decimal import Decimal as D
    broker=PaperBroker(fee_bps=D('10'),slippage_bps=D('20'))
    fill=broker.fill_market('BUY',D('2'),D('99'),D('100'),latency_ms=73,available_qty=D('0.5'))
    assert fill.qty==D('0.5')
    assert fill.price>D('100')
    assert fill.latency_ms==73


def test_phase134_stale_data_banner_state_is_executed_with_local_typescript_fixture():
    tsc=shutil.which('tsc'); node=shutil.which('node')
    assert tsc and node
    with tempfile.TemporaryDirectory() as td:
        out=Path(td)/'out'; out.mkdir()
        subprocess.run([tsc,'frontend/src/ux/dataHealth.ts','--target','ES2022','--module','ES2022','--moduleResolution','Bundler','--skipLibCheck','--outDir',str(out)],cwd=ROOT,check=True,capture_output=True,text=True,timeout=30)
        mod=(out/'dataHealth.js').as_uri()
        h=Path(td)/'check.mjs'
        h.write_text(f"import {{dataHealthPresentation}} from {json.dumps(mod)}; const stale=dataHealthPresentation({{stale:true,needsResync:false,ageMs:12500}}); const gap=dataHealthPresentation({{stale:true,needsResync:true,ageMs:1,reason:'SEQUENCE_GAP'}}); if(!stale.blocking||stale.severity!=='warning'||!stale.label.includes('GÜNCEL DEĞİL'))process.exit(2); if(!gap.blocking||gap.severity!=='error'||!gap.label.includes('SEQUENCE_GAP'))process.exit(3); console.log('ok');",encoding='utf-8')
        run=subprocess.run([node,str(h)],cwd=ROOT,capture_output=True,text=True,timeout=30)
        assert run.returncode==0,run.stderr+run.stdout
    status=(ROOT/'frontend/src/components/StatusStrip.tsx').read_text(encoding='utf-8')
    assert 'dataHealthPresentation' in status and 'Yeni risk artırıcı kararlar' in status and 'role="alert"' in status


def test_phase134_final_system_conformance_keeps_real_code_local_fixture_boundary_and_paper_default():
    assert Settings().mode is TradingMode.PAPER
    required=[
        'backend/app/data/point_in_time.py',
        'backend/app/universe',
        'backend/app/backtest',
        'backend/app/research/time_validation.py',
        'backend/app/paper/engine.py',
        'backend/app/exchange/binance.py',
        'backend/app/risk/live_ramp.py',
        'backend/app/monitoring/telegram.py',
        'backend/app/strategies/levels.py',
        'backend/app/signals/decision_quality.py',
        'frontend/public/manifest.webmanifest',
        'frontend/public/sw.js',
        'frontend/src-tauri/tauri.conf.json',
    ]
    for rel in required: assert (ROOT/rel).exists(), rel
    compose=(ROOT/'docker-compose.yml').read_text(encoding='utf-8').lower()
    assert 'backend' in compose and 'frontend' in compose and 'postgres' in compose and 'redis' in compose
    source='\n'.join((ROOT/p).read_text(encoding='utf-8',errors='ignore') for p in [
        'backend/app/research/time_validation.py','backend/app/strategies/levels.py','backend/app/signals/decision_quality.py','backend/app/signals/engine.py','frontend/src/runtime/clientShell.ts'
    ])
    for token in ('purged_embargo_split','nested_walk_forward','trailing','NO_TRADE','isClientCompatible'):
        assert token.lower() in source.lower()
    # External production evidence remains a separate gate; conformance must not imply LIVE enablement.
    gate=(ROOT/'docs/FINAL_DELIVERY_STATUS.md').read_text(encoding='utf-8')
    assert 'PAPER' in gate and 'fail-closed' in gate
