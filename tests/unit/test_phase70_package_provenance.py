import json
import zipfile
from hashlib import sha256
from pathlib import Path

import scripts.package_distribution as pd


def _sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _write_distribution(path: Path, manifest: dict, source: bytes, evidence: bytes) -> None:
    manifest = {"schema_version": "1.0", **manifest}
    checks = "".join(
        f"{row['sha256']}  {row['name']}\n"
        for row in manifest.get("artifacts", [])
    ).encode()
    with zipfile.ZipFile(path, "w") as z:
        z.writestr(pd.BUNDLE_MANIFEST, json.dumps(manifest))
        z.writestr("source.zip", source)
        z.writestr("evidence.zip", evidence)
        z.writestr("SHA256SUMS.txt", checks)



def test_package_provenance_binds_final_distribution_hash(tmp_path, monkeypatch):
    root = tmp_path / "root"; root.mkdir()
    release = root / "RELEASE_MANIFEST.json"
    release.write_text(json.dumps({
        "git_commit_sha": "abc", "ci_run_id": "LOCAL-NOT-CI", "prod_live_status": "BLOCKED",
        "default_mode": "PAPER", "live_enabled": False, "source_tree_hash": "s"
    }))
    source = b"s"; evidence = b"ev"
    monkeypatch.setattr(pd, "git_sha", lambda root=None: "abc")
    manifest = {"git_commit_sha": "abc", "live_enabled": False, "default_mode": "PAPER", "artifacts": [
        {"role": "source", "name": "source.zip", "sha256": sha256(source).hexdigest(), "size": len(source)},
        {"role": "evidence", "name": "evidence.zip", "sha256": sha256(evidence).hexdigest(), "size": len(evidence)},
    ]}
    distribution = tmp_path / "bundle.zip"
    manifest = {"schema_version": "1.0", **manifest}
    _write_distribution(distribution, manifest, source, evidence)
    out = tmp_path / "PACKAGE_PROVENANCE.json"
    payload = pd.build_package_provenance(root=root, distribution=distribution, bundle_manifest=manifest, output=out)
    assert payload["classification"] == "LOCAL_PACKAGE_PROVENANCE_NOT_CI_PROVENANCE"
    assert payload["distribution_archive"]["sha256"] == _sha(distribution)
    assert pd.verify_package_provenance(out, root=root)["verified"]
    with distribution.open("ab") as fh: fh.write(b"tamper")
    assert "DISTRIBUTION_ARCHIVE_HASH_MISMATCH" in pd.verify_package_provenance(out, root=root)["problems"]


def test_package_provenance_never_upgrades_live_status(tmp_path, monkeypatch):
    root = tmp_path / "root"; root.mkdir()
    release = root / "RELEASE_MANIFEST.json"
    release.write_text(json.dumps({"git_commit_sha":"abc","ci_run_id":"LOCAL-NOT-CI","prod_live_status":"BLOCKED","default_mode":"PAPER","live_enabled":False}))
    distribution = tmp_path / "bundle.zip"; distribution.write_bytes(b"zip")
    monkeypatch.setattr(pd, "git_sha", lambda root=None: "abc")
    out = tmp_path / "PACKAGE_PROVENANCE.json"
    payload = pd.build_package_provenance(root=root, distribution=distribution, bundle_manifest={"git_commit_sha":"abc","artifacts":[]}, output=out)
    assert payload["release_status"]["prod_live_status"] == "BLOCKED"
    assert payload["release_status"]["live_enabled"] is False


def test_package_provenance_detects_embedded_source_evidence_mismatch(tmp_path, monkeypatch):
    root = tmp_path / "root"; root.mkdir()
    release = root / "RELEASE_MANIFEST.json"
    release.write_text(json.dumps({"git_commit_sha":"abc","ci_run_id":"LOCAL-NOT-CI","prod_live_status":"BLOCKED","default_mode":"PAPER","live_enabled":False}))
    monkeypatch.setattr(pd, "git_sha", lambda root=None: "abc")
    source = b"source"; evidence = b"evidence"
    bundle = {
        "git_commit_sha":"abc", "live_enabled":False, "default_mode":"PAPER",
        "artifacts":[
            {"role":"source","name":"source.zip","sha256":sha256(source).hexdigest(),"size":len(source)},
            {"role":"evidence","name":"evidence.zip","sha256":sha256(evidence).hexdigest(),"size":len(evidence)},
        ]
    }
    distribution = tmp_path / "bundle.zip"
    bundle = {"schema_version": "1.0", **bundle}
    _write_distribution(distribution, bundle, source, evidence)
    out = tmp_path / "PACKAGE_PROVENANCE.json"
    pd.build_package_provenance(root=root, distribution=distribution, bundle_manifest=bundle, output=out)
    assert pd.verify_package_provenance(out, root=root)["verified"]
    doc = json.loads(out.read_text())
    doc["source_archive"]["sha256"] = "0" * 64
    out.write_text(json.dumps(doc))
    result = pd.verify_package_provenance(out, root=root)
    assert "SOURCE_ARCHIVE_PROVENANCE_MISMATCH" in result["problems"]
