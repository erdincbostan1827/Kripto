from __future__ import annotations

from pathlib import Path
import runpy
import sys


def test_acceptance_challenge_entrypoint_bootstraps_backend_path(monkeypatch) -> None:
    root = Path(__file__).resolve().parents[1]
    backend = root / "backend"
    script = root / "scripts" / "generate_acceptance_challenge.py"

    backend_resolved = backend.resolve()
    sanitized_path: list[str] = []
    for entry in sys.path:
        try:
            if Path(entry or ".").resolve() == backend_resolved:
                continue
        except OSError:
            pass
        sanitized_path.append(entry)
    monkeypatch.setattr(sys, "path", sanitized_path)

    for module_name in list(sys.modules):
        if (
            module_name == "app"
            or module_name.startswith("app.")
            or module_name == "backend.app.release.acceptance_challenge"
        ):
            monkeypatch.delitem(sys.modules, module_name, raising=False)

    namespace = runpy.run_path(str(script), run_name="phase253_import_probe")

    assert callable(namespace["create_challenge"])
    assert str(backend) in sys.path
