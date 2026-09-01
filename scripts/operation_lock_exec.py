from __future__ import annotations
import argparse, json, os, sys, time
from pathlib import Path

_IMPORT_ROOT = Path(__file__).resolve().parents[1]
if str(_IMPORT_ROOT) not in sys.path:
    sys.path.insert(0, str(_IMPORT_ROOT))

try:
    from scripts.operation_lock import operation_lock
    from scripts.bounded_subprocess import guard_process_signals, start_process_group, terminate_process_tree
except ModuleNotFoundError:
    from operation_lock import operation_lock
    from bounded_subprocess import guard_process_signals, start_process_group, terminate_process_tree


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
        proc=start_process_group(cmd, env=env)
        try:
            with guard_process_signals(proc):
                while proc.poll() is None:
                    time.sleep(a.heartbeat_check_seconds)
                    held['assert_healthy']()
                # A leader may exit while descendants in its process group remain
                # active. Quiesce the entire tree before releasing the platform
                # operation lock so no deployment work can outlive the mutex.
                terminate_process_tree(proc)
                held['assert_healthy']()
                return int(proc.returncode)
        except BaseException:
            # Always target the process group, even when the direct leader has
            # already exited; descendants may still be alive.
            terminate_process_tree(proc)
            raise
if __name__=='__main__': raise SystemExit(main())
