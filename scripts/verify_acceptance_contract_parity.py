from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
WORKFLOW = ROOT / ".github" / "workflows" / "production-acceptance.yml"


def _workflow_contract(text: str) -> tuple[set[str], set[str]]:
    secrets = set(re.findall(r"secrets\.([A-Z0-9_]+)", text))
    variables = set(re.findall(r"vars\.([A-Z0-9_]+)", text))
    return secrets, variables


def verify(root: Path = ROOT) -> dict:
    problems: list[str] = []
    workflow = (root / ".github" / "workflows" / "production-acceptance.yml").read_text(encoding="utf-8")
    workflow_secrets, workflow_vars = _workflow_contract(workflow)

    import scripts.production_acceptance_handoff as handoff
    expected_secrets = set(handoff.REQUIRED_SECRETS)
    expected_vars = set(handoff.REQUIRED_ENVIRONMENT_VARS)

    if workflow_secrets != expected_secrets:
        problems.append(
            "WORKFLOW_HANDOFF_SECRET_SET_MISMATCH:"
            f"workflow={sorted(workflow_secrets)}:handoff={sorted(expected_secrets)}"
        )
    if workflow_vars != expected_vars:
        problems.append(
            "WORKFLOW_HANDOFF_VAR_SET_MISMATCH:"
            f"workflow={sorted(workflow_vars)}:handoff={sorted(expected_vars)}"
        )

    preflight_text = (root / "scripts" / "external_acceptance_preflight.py").read_text(encoding="utf-8")
    preflight_envs = set(re.findall(r'_env\("([A-Z0-9_]+)"\)', preflight_text))
    required_preflight = workflow_secrets | workflow_vars
    missing_preflight = sorted(required_preflight - preflight_envs)
    if missing_preflight:
        problems.append("PREFLIGHT_CONTRACT_MISSING:" + ",".join(missing_preflight))

    return {
        "schema_version": "1.0",
        "classification": "PRODUCTION_ACCEPTANCE_CONTRACT_PARITY",
        "verified": not problems,
        "problems": problems,
        "workflow_secrets": sorted(workflow_secrets),
        "workflow_environment_vars": sorted(workflow_vars),
        "handoff_secrets": sorted(expected_secrets),
        "handoff_environment_vars": sorted(expected_vars),
        "preflight_envs": sorted(preflight_envs),
    }


def main() -> int:
    result = verify()
    out = ROOT / "reports" / "ACCEPTANCE_CONTRACT_PARITY.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0 if result["verified"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
