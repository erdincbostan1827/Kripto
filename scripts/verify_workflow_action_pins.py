from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"
USES_RE = re.compile(r"^\s*-?\s*uses:\s*([^\s#]+)", re.M)
SHA_REF_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_./-]+)?@[0-9a-f]{40}$")
DOCKER_DIGEST_RE = re.compile(r"^docker://[^@\s]+@sha256:[0-9a-f]{64}$")


def verify_workflow_action_pins(root: Path = ROOT) -> dict:
    problems: list[str] = []
    checked: list[str] = []
    workflow_dir = root / ".github" / "workflows"
    for path in sorted(workflow_dir.glob("*.y*ml")):
        text = path.read_text(encoding="utf-8")
        for ref in USES_RE.findall(text):
            if ref.startswith("./"):
                continue
            checked.append(f"{path.relative_to(root)}:{ref}")
            if ref.startswith("docker://"):
                if not DOCKER_DIGEST_RE.fullmatch(ref):
                    problems.append(f"UNPINNED_CONTAINER_ACTION:{path.relative_to(root)}:{ref}")
            elif not SHA_REF_RE.fullmatch(ref):
                problems.append(f"UNPINNED_ACTION:{path.relative_to(root)}:{ref}")
    return {"verified": not problems, "problems": problems, "checked_action_count": len(checked), "checked": checked}


def main() -> int:
    result = verify_workflow_action_pins()
    print(f"WORKFLOW_ACTION_PINS={'PASS' if result['verified'] else 'FAIL'}")
    print(f"checked_action_count={result['checked_action_count']}")
    for p in result["problems"]:
        print(f"- {p}")
    return 0 if result["verified"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
