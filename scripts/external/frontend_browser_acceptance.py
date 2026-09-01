from __future__ import annotations

import argparse
import json
import os
import shutil
import socket
import subprocess
import sys
import time
from contextlib import closing
from hashlib import sha256
from datetime import datetime, timezone
from pathlib import Path

_IMPORT_ROOT = Path(__file__).resolve().parents[2]
if str(_IMPORT_ROOT) not in sys.path:
    sys.path.insert(0, str(_IMPORT_ROOT))
from scripts.bounded_subprocess import run_captured

ROOT = _IMPORT_ROOT
FRONTEND = ROOT / "frontend"
REPORTS = ROOT / "reports" / "external_acceptance"
OUT = REPORTS / "frontend_browser_acceptance.json"

VIEWPORTS = ((1920,1080),(1366,768),(1024,768),(390,844))


def _sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _run(cmd: list[str], *, cwd: Path = ROOT, timeout: int = 300) -> dict:
    tool = shutil.which(cmd[0])
    if not tool:
        return {"command": cmd, "exit_code": None, "status": "BLOCKED", "blocker": f"TOOL_UNAVAILABLE:{cmd[0]}", "output": ""}
    try:
        p = run_captured(cmd, cwd=cwd, timeout=timeout)
        return {"command": cmd, "exit_code": p.returncode, "status": "PASS" if p.returncode == 0 else "BLOCKED", "blocker": None if p.returncode == 0 else f"EXIT_CODE:{p.returncode}", "output": (p.stdout or "")[-12000:]}
    except subprocess.TimeoutExpired as exc:
        out = exc.stdout.decode(errors="replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        return {"command": cmd, "exit_code": None, "status": "BLOCKED", "blocker": "TIMEOUT", "output": out[-12000:]}


def _free_port() -> int:
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


def _git_sha() -> str | None:
    try:
        p = run_captured(["git", "rev-parse", "HEAD"], cwd=ROOT, timeout=10)
        value = (p.stdout or "").strip().lower()
        return value if p.returncode == 0 and len(value) == 40 else None
    except Exception:
        return None


def run(*, timeout: int = 300, confirm_real: bool = False) -> dict:
    REPORTS.mkdir(parents=True, exist_ok=True)
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    run_dir = REPORTS / "frontend_browser_runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=False)
    blockers: list[str] = []
    evidence: dict[str, object] = {}
    if not confirm_real:
        blockers.append("REAL_TARGET_NOT_EXPLICITLY_CONFIRMED")
    lock = FRONTEND / "package-lock.json"
    if not lock.is_file():
        blockers.append("FRONTEND_LOCK_MISSING")
    chromium = shutil.which("chromium") or shutil.which("chromium-browser") or shutil.which("google-chrome")
    chromium_version = None
    if not chromium:
        blockers.append("CHROMIUM_UNAVAILABLE")
    else:
        version = _run([chromium, "--version"], timeout=min(timeout, 30))
        evidence["chromium_version"] = version
        chromium_version = (version.get("output") or "").strip() if version.get("status") == "PASS" else None
        if not chromium_version:
            blockers.append("CHROMIUM_VERSION_NOT_VERIFIED")

    # npm ci is mandatory: never silently use an unbound node_modules tree.
    ci = _run(["npm", "ci", "--ignore-scripts"], cwd=FRONTEND, timeout=timeout) if (confirm_real and lock.is_file()) else {"status":"BLOCKED","blocker":"REAL_TARGET_NOT_EXPLICITLY_CONFIRMED" if not confirm_real else "FRONTEND_LOCK_MISSING"}
    evidence["npm_ci"] = ci
    if ci.get("status") != "PASS": blockers.append(str(ci.get("blocker") or "NPM_CI_FAILED"))

    unit = _run(["npm", "test", "--", "--run"], cwd=FRONTEND, timeout=timeout) if ci.get("status") == "PASS" else {"status":"BLOCKED","blocker":"NPM_CI_NOT_PASS"}
    evidence["vitest"] = unit
    if unit.get("status") != "PASS": blockers.append(str(unit.get("blocker") or "VITEST_FAILED"))

    build = _run(["npm", "run", "build"], cwd=FRONTEND, timeout=timeout) if ci.get("status") == "PASS" else {"status":"BLOCKED","blocker":"NPM_CI_NOT_PASS"}
    evidence["production_build"] = build
    dist = FRONTEND / "dist"
    if build.get("status") != "PASS" or not (dist / "index.html").is_file(): blockers.append("PRODUCTION_BUILD_NOT_VERIFIED")

    browser_rows: list[dict] = []
    if not blockers and chromium:
        port = _free_port()
        server = subprocess.Popen([sys.executable, "-m", "http.server", str(port), "--bind", "127.0.0.1"], cwd=dist, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            time.sleep(0.5)
            for w,h in VIEWPORTS:
                shot = run_dir / f"viewport_{w}x{h}.png"
                dom = run_dir / f"viewport_{w}x{h}.html"
                url = f"http://127.0.0.1:{port}/"
                cmd = [chromium, "--headless=new", "--no-sandbox", "--disable-gpu", f"--window-size={w},{h}", f"--screenshot={shot}", url]
                row = _run(cmd, timeout=min(timeout,120))
                dom_row = _run([chromium, "--headless=new", "--no-sandbox", "--disable-gpu", "--dump-dom", url], timeout=min(timeout,120))
                dom_text = dom_row.get("output") or ""
                dom.write_text(dom_text, encoding="utf-8")
                root_rendered = bool(dom_row.get("status") == "PASS" and '<div id="root">' in dom_text and len(dom_text) > 500)
                row["viewport"] = f"{w}x{h}"
                row["screenshot_path"] = str(shot.relative_to(ROOT)) if shot.is_file() else None
                row["screenshot_bytes"] = shot.stat().st_size if shot.is_file() else 0
                row["screenshot_sha256"] = _sha(shot) if shot.is_file() else None
                row["dom_path"] = str(dom.relative_to(ROOT))
                row["dom_sha256"] = _sha(dom)
                row["root_rendered"] = root_rendered
                if row.get("status") != "PASS" or not shot.is_file() or shot.stat().st_size < 1000 or not root_rendered:
                    blockers.append(f"CHROMIUM_VIEWPORT_FAILED:{w}x{h}")
                browser_rows.append(row)
        finally:
            server.terminate()
            try: server.wait(timeout=5)
            except subprocess.TimeoutExpired: server.kill()
    evidence["chromium_viewports"] = browser_rows

    payload = {
        "schema_version": "1.1",
        "classification": "REAL_DEPENDENCY_RESOLVED_FRONTEND_BROWSER_ACCEPTANCE",
        "truth_policy": "PASS requires explicit real-target confirmation, lock-bound npm ci, Vitest, production build, persistent DOM/screenshot evidence, and real headless Chromium renders at every required viewport. It does not claim Edge/Firefox/WebKit coverage.",
        "real_target_explicitly_confirmed": bool(confirm_real),
        "run_id": run_id,
        "run_directory": str(run_dir.relative_to(ROOT)),
        "git_commit_sha": _git_sha(),
        "verified": not blockers,
        "blockers": sorted(set(blockers)),
        "frontend_lock_sha256": _sha(lock) if lock.is_file() else None,
        "dist_index_sha256": _sha(dist / "index.html") if (dist / "index.html").is_file() else None,
        "chromium_path": chromium,
        "chromium_version": chromium_version,
        "viewports": [f"{w}x{h}" for w,h in VIEWPORTS],
        "evidence": evidence,
    }
    immutable = run_dir / "manifest.json"
    immutable.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    payload["manifest_sha256"] = _sha(immutable)
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def main() -> int:
    p=argparse.ArgumentParser(description="Fail-closed dependency-resolved frontend/browser acceptance")
    p.add_argument("--timeout", type=int, default=300)
    p.add_argument("--confirm-real-target", action="store_true", help="Explicitly confirm execution against the intended real dependency/browser acceptance target.")
    args=p.parse_args()
    result=run(timeout=max(1,args.timeout), confirm_real=args.confirm_real_target)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["verified"] else 2

if __name__ == "__main__":
    raise SystemExit(main())
