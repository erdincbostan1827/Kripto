from __future__ import annotations
import argparse, json, os, tempfile
from datetime import datetime, timezone
from pathlib import Path

try:
    from scripts.database_migration_guard import _canonical_hash, _environment_fingerprint, _sha256_file, verify_restore_drill_receipt
    from scripts.transactional_release_update import _tree_sha256
except ModuleNotFoundError:
    from database_migration_guard import _canonical_hash, _environment_fingerprint, _sha256_file, verify_restore_drill_receipt
    from transactional_release_update import _tree_sha256


def _atomic_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2, sort_keys=True); fh.write("\n"); fh.flush(); os.fsync(fh.fileno())
        os.replace(tmp, path)
    except BaseException:
        try: os.unlink(tmp)
        except FileNotFoundError: pass
        raise


def create_receipt(*, backup: Path, restore_drill_receipt: Path, active: Path, migration_head: str, environment_id: str, output: Path) -> dict:
    backup=backup.resolve(); restore_drill_receipt=restore_drill_receipt.resolve(); active=active.resolve(); output=output.resolve()
    env_fp=_environment_fingerprint(environment_id)
    if backup.is_symlink() or not backup.is_file(): raise RuntimeError("DATABASE_BACKUP_ARTIFACT_MISSING_OR_UNSAFE")
    if restore_drill_receipt.parent != output.parent: raise RuntimeError("DATABASE_BACKUP_RESTORE_RECEIPT_MUST_SHARE_OUTPUT_DIRECTORY")
    backup_hash=_sha256_file(backup)
    restore=verify_restore_drill_receipt(restore_drill_receipt, expected_backup_sha256=backup_hash, expected_environment_id=environment_id)
    body={
      "schema_version":"1.1", "classification":"VERIFIED_DATABASE_BACKUP_RECEIPT",
      "migration_head":migration_head, "active_tree_sha256":_tree_sha256(active),
      "backup_artifact":os.path.relpath(backup, output.parent), "backup_sha256":backup_hash,
      "restore_drill_receipt":restore_drill_receipt.name, "restore_drill_receipt_sha256":_sha256_file(restore_drill_receipt),
      "restore_drill_provenance_sha256":restore["provenance_sha256"],
      "environment_id":environment_id.strip(), "environment_fingerprint":env_fp,
      "created_at":datetime.now(timezone.utc).isoformat(),
      "policy":"BACKUP_ACCEPTABLE_FOR_MIGRATION_ONLY_AFTER_FRESH_HASH_AND_ENVIRONMENT_BOUND_RESTORE_DRILL_PASS",
    }
    body["provenance_sha256"]=_canonical_hash(body)
    _atomic_json(output, body)
    return {"created":True,"output":str(output),"backup_sha256":backup_hash,"restore_drill_receipt_sha256":_sha256_file(restore_drill_receipt),"environment_fingerprint":env_fp,"provenance_sha256":body["provenance_sha256"]}


def main()->int:
    p=argparse.ArgumentParser(); p.add_argument('--backup',type=Path,required=True); p.add_argument('--restore-drill-receipt',type=Path,required=True); p.add_argument('--active',type=Path,required=True); p.add_argument('--migration-head',required=True); p.add_argument('--environment-id',required=True); p.add_argument('--output',type=Path,required=True)
    a=p.parse_args(); print(json.dumps(create_receipt(backup=a.backup,restore_drill_receipt=a.restore_drill_receipt,active=a.active,migration_head=a.migration_head,environment_id=a.environment_id,output=a.output),sort_keys=True)); return 0
if __name__=='__main__': raise SystemExit(main())
