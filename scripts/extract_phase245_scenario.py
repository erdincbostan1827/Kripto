from __future__ import annotations

import json
import sys
from pathlib import Path


REQUIRED_CHECKS = ("market_order", "limit_order", "cancel", "partial_fill")


def extract_scenario(text: str) -> dict | None:
    """Return the last Phase245 scenario JSON object embedded in mixed process logs."""
    decoder = json.JSONDecoder()
    candidates: list[dict] = []
    for index, char in enumerate(text):
        if char != "{":
            continue
        try:
            value, _ = decoder.raw_decode(text[index:])
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict) and "all_pass" in value and "endpoint" in value:
            candidates.append(value)
    if not candidates:
        return None

    scenario = dict(candidates[-1])
    checks = scenario.get("checks")
    if not isinstance(checks, dict):
        checks = {}
    check_failed = bool(0)
    normalized_checks: dict[str, dict] = {}
    for key in REQUIRED_CHECKS:
        raw = checks.get(key)
        normalized_checks[key] = (
            dict(raw)
            if isinstance(raw, dict)
            else {"pass": check_failed, "status": "NOT_REPORTED"}
        )
        normalized_checks[key].setdefault("pass", check_failed)
    scenario["checks"] = normalized_checks
    scenario.setdefault("symbol", "")
    scenario.setdefault("symbol_selection_mode", "")
    scenario.setdefault("partial_price_mode", "")
    return scenario


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) != 2:
        print("usage: extract_phase245_scenario.py <mixed-log> <output-json>", file=sys.stderr)
        return 2

    source = Path(args[0])
    target = Path(args[1])
    if not source.is_file():
        print("Phase245 scenario source log is missing", file=sys.stderr)
        return 2

    scenario = extract_scenario(source.read_text(encoding="utf-8", errors="replace"))
    if scenario is None:
        print("Phase245 scenario JSON was not found in mixed log", file=sys.stderr)
        return 2

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(scenario, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
