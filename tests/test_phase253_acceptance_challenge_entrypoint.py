from __future__ import annotations

from pathlib import Path
import runpy
import sys


def _sanitize_backend_import_state(monkeypatch, root: Path) -> Path:
    backend = root / "backend"
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
            or module_name == "backend.app.release.acceptance_contract"
            or module_name == "backend.app.release.evidence_ledger"
        ):
            monkeypatch.delitem(sys.modules, module_name, raising=False)
    return backend


def test_acceptance_challenge_entrypoint_bootstraps_backend_path(monkeypatch) -> None:
    root = Path(__file__).resolve().parents[1]
    backend = _sanitize_backend_import_state(monkeypatch, root)
    script = root / "scripts" / "generate_acceptance_challenge.py"

    namespace = runpy.run_path(str(script), run_name="phase253_import_probe")

    assert callable(namespace["create_challenge"])
    assert str(backend) in sys.path


def test_external_acceptance_runner_bootstraps_backend_path(monkeypatch) -> None:
    root = Path(__file__).resolve().parents[1]
    backend = _sanitize_backend_import_state(monkeypatch, root)
    script = root / "scripts" / "external_acceptance_runner.py"

    namespace = runpy.run_path(str(script), run_name="phase256_import_probe")

    assert callable(namespace["execute"])
    assert callable(namespace["verify_challenge"])
    assert str(backend) in sys.path
