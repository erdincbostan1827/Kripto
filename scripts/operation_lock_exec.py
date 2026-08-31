from __future__ import annotations
import argparse, json, os, subprocess, time
from pathlib import Path
try:
    from scripts.operation_lock import operation_lock
except ModuleNotFoundError:
    from operation_lock import operation_lock

def main()->int:
    p=argparse.ArgumentParser(description='Execute one command while holding the platform deployment operation lock.')
    p.add_argument('--lock-dir',type=Path,required=True); p.add_argument('--operation',required=True); p.add_argument('--env-json'); p.add_argument('--heartbeat-check-seconds',type=float,default=0.25); p.add_argument('command',nargs=argparse.REMAINDER)
    a=p.parse_args(); cmd=list(a.command)
    if cmd and cmd[0]=='--': cmd=cmd[1:]
    if not cmd or any(not x or '\x00' in x for x in cmd): raise SystemExit('OPERATION_LOCK_EXEC_COMMAND_INVALID')
    if not 0.05 <= a.heartbeat_check_seconds <= 30: raise SystemExit('OPERATION_LOCK_EXEC_HEARTBEAT_CHECK_INVALID')
    env=os.environ.copy()
    if a.env_json:
        extra=json.loads(a.env_json)
        if not isinstance(extra,dict) or any(not isinstance(k,str) or not isinstance(v,str) for k,v in extra.items()): raise SystemExit('OPERATION_LOCK_EXEC_ENV_INVALID')
        env.update(extra)
    with operation_lock(a.lock_dir, operation=a.operation) as held:
        proc=subprocess.Popen(cmd,shell=False,env=env)
        try:
            while proc.poll() is None:
                time.sleep(a.heartbeat_check_seconds)
                try:
                    held['assert_healthy']()
                except BaseException:
                    proc.terminate()
                    try: proc.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        proc.kill(); proc.wait(timeout=5)
                    raise
            held['assert_healthy']()
            return int(proc.returncode)
        except BaseException:
            if proc.poll() is None:
                proc.kill(); proc.wait(timeout=5)
            raise
if __name__=='__main__': raise SystemExit(main())
