from pathlib import Path
import json, os, shutil, subprocess, tempfile

ROOT=Path(__file__).resolve().parents[2]

def test_phase132_frontend_realtime_state_memory_soak_has_bounded_heap_growth():
    tsc=shutil.which('tsc')
    node=shutil.which('node')
    assert tsc and node, 'local frontend memory acceptance requires tsc and node'
    with tempfile.TemporaryDirectory() as td:
        out=Path(td)/'out'; out.mkdir()
        subprocess.run([
            tsc,'frontend/src/realtime/versionedState.ts','--target','ES2022','--module','ES2022',
            '--moduleResolution','Bundler','--lib','ES2022,DOM','--skipLibCheck','--outDir',str(out)
        ],cwd=ROOT,check=True,capture_output=True,text=True,timeout=60)
        harness=Path(td)/'soak.mjs'
        module=(out/'versionedState.js').as_uri()
        harness.write_text(f'''import {{initialRealtimeState,applySnapshot,applyIncremental}} from {json.dumps(module)};\nif(!global.gc)throw new Error('GC_NOT_EXPOSED');\nconst payload=(i)=>({{symbol:'BTCUSDT',price:i,rows:Array.from({{length:32}},(_,j)=>i+j)}});\nlet s=applySnapshot(initialRealtimeState(),{{sequence:0,version:'v1',receivedAt:0,sourceTime:0,payload:payload(0)}});\nfor(let i=1;i<=5000;i++)s=applyIncremental(s,{{sequence:i,version:'v1',receivedAt:i,sourceTime:i,payload:payload(i)}});\nglobal.gc(); global.gc(); const base=process.memoryUsage().heapUsed;\nfor(let round=0;round<20;round++){{for(let i=1;i<=5000;i++)s=applySnapshot(s,{{sequence:i,version:'v1',receivedAt:i,sourceTime:i,payload:payload(i)}});global.gc();}}\nglobal.gc(); global.gc(); const end=process.memoryUsage().heapUsed; const growth=Math.max(0,end-base);\nconsole.log(JSON.stringify({{base,end,growth,budget:8_000_000,sequence:s.snapshot.sequence}}));\nif(growth>8_000_000)process.exit(2);\n''',encoding='utf-8')
        run=subprocess.run([node,'--expose-gc',str(harness)],cwd=ROOT,check=False,capture_output=True,text=True,timeout=60)
        assert run.returncode==0, run.stderr+run.stdout
        result=json.loads(run.stdout.strip().splitlines()[-1])
        assert result['growth']<=result['budget']
        assert result['sequence']==5000
