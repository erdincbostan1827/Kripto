from __future__ import annotations
from dataclasses import dataclass,asdict
from pathlib import Path
import hashlib,json,shutil

TOOLS=('pip-audit','trivy','gitleaks','bandit','semgrep','cyclonedx-py','syft')

@dataclass(frozen=True)
class SupplyChainEvidence:
    tool_availability:dict[str,bool]
    python_lock_present:bool
    frontend_lock_present:bool
    sbom_present:bool
    vulnerability_report_present:bool
    sast_report_present:bool
    license_report_present:bool
    secret_scan_report_present:bool

    def production_blockers(self)->tuple[str,...]:
        blockers=[]
        if not self.python_lock_present: blockers.append('PYTHON_LOCK_MISSING')
        if not self.frontend_lock_present: blockers.append('FRONTEND_LOCK_MISSING')
        if not self.sbom_present: blockers.append('SBOM_MISSING')
        if not self.vulnerability_report_present: blockers.append('VULNERABILITY_SCAN_MISSING')
        if not self.sast_report_present: blockers.append('SAST_MISSING')
        if not self.license_report_present: blockers.append('LICENSE_REPORT_MISSING')
        if not self.secret_scan_report_present: blockers.append('SECRET_SCAN_EVIDENCE_MISSING')
        return tuple(blockers)

    def fingerprint(self)->str:
        b=json.dumps(asdict(self),sort_keys=True,separators=(',',':')).encode()
        return hashlib.sha256(b).hexdigest()


def collect_supply_chain_evidence(root:Path)->SupplyChainEvidence:
    reports=root/'reports'
    sbom=any((root/p).exists() for p in ('sbom.cdx.json','SBOM.json','reports/SBOM.json'))
    return SupplyChainEvidence(
        tool_availability={t:bool(shutil.which(t)) for t in TOOLS},
        python_lock_present=(root/'uv.lock').exists(),
        frontend_lock_present=(root/'frontend/package-lock.json').exists(),
        sbom_present=sbom,
        vulnerability_report_present=any((reports/p).exists() for p in ('VULNERABILITY_SCAN.json','VULNERABILITY_SCAN.txt')),
        sast_report_present=any((reports/p).exists() for p in ('SAST.json','SAST.txt')),
        license_report_present=any((reports/p).exists() for p in ('LICENSE_REPORT.json','LICENSE_REPORT.txt')),
        secret_scan_report_present=(reports/'LATEST_SECRET_SCAN.txt').exists(),
    )
