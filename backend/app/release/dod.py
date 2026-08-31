from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class DefinitionOfDoneEvidence:
    implementation_exists:bool; static_type_lint_passed:bool; required_tests_passed:bool; extended_tests_passed_or_not_required:bool
    evidence_reference:str|None; documentation_or_runbook_present_or_not_required:bool; uses_mock:bool; mock_disclosed:bool; known_critical_issues:tuple[str,...]
    machine_readable_matrix_present:bool; delivery_artifacts_present:bool
    def blockers(self)->tuple[str,...]:
        b=[]
        checks=((self.implementation_exists,"IMPLEMENTATION_MISSING"),(self.static_type_lint_passed,"STATIC_TYPE_LINT_NOT_PASS"),(self.required_tests_passed,"REQUIRED_TESTS_NOT_PASS"),(self.extended_tests_passed_or_not_required,"EXTENDED_TESTS_NOT_PASS"),(bool(self.evidence_reference),"EVIDENCE_REFERENCE_MISSING"),(self.documentation_or_runbook_present_or_not_required,"DOCS_RUNBOOK_MISSING"),(self.machine_readable_matrix_present,"MACHINE_READABLE_MATRIX_MISSING"),(self.delivery_artifacts_present,"DELIVERY_ARTIFACTS_MISSING"))
        b.extend(reason for ok,reason in checks if not ok)
        if self.uses_mock and not self.mock_disclosed: b.append("MOCK_NOT_DISCLOSED")
        if self.known_critical_issues: b.append("KNOWN_CRITICAL_ISSUE")
        return tuple(b)
    def assert_done(self):
        b=self.blockers()
        if b: raise RuntimeError("definition of done blocked: "+",".join(b))
