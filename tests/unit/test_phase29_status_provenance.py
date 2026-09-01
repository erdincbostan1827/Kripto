import json, re
from pathlib import Path
import yaml
from scripts.generate_project_status import build, render

def test_generated_status_counts_match_matrix_and_remains_fail_closed():
 s=build(); rows=yaml.safe_load(Path('requirements_acceptance_matrix.yaml').read_text())['requirements']
 assert s['requirements']['total']==len(rows)
 assert sum(s['requirements']['counts'].values())==len(rows)
 assert s['prod_live_status']=='BLOCKED' and s['live_enabled'] is False and s['default_mode']=='PAPER'
 assert 'tests collected' in render(s)

def test_known_issues_is_generated_not_stale_hardcoded_snapshot():
 s=build(); text=render(s)
 assert f"{s['requirements']['p0_total']} total" in text
 assert f"{s['test_count']} tests collected" in text
 assert '285/285 PASS' not in text

def test_local_provenance_schema_never_conflates_local_with_ci():
 p=Path('reports/LOCAL_SOURCE_PROVENANCE.json')
 if not p.exists(): return
 d=json.loads(p.read_text())
 assert d['classification']=='LOCAL_SOURCE_PROVENANCE_NOT_CI_PROVENANCE'
 if d['git_commit_sha']!='UNAVAILABLE': assert re.fullmatch(r'[0-9a-f]{40}',d['git_commit_sha'])


def test_python_and_frontend_direct_dependencies_are_exactly_pinned():
 import tomllib
 py=tomllib.loads(Path('pyproject.toml').read_text())
 for dep in py['project']['dependencies'] + py['project']['optional-dependencies']['test']:
  assert '==' in dep and '>=' not in dep and '<' not in dep
 pkg=json.loads(Path('frontend/package.json').read_text())
 for group in ('dependencies','devDependencies'):
  for version in pkg[group].values():
   assert re.fullmatch(r'\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?', version)

def test_test_suite_has_required_local_safety_and_recovery_categories():
 required=[
  Path('tests/unit'), Path('tests/integration'), Path('tests/property'), Path('tests/safety'),
  Path('tests/integration/test_restart_recovery.py'), Path('tests/integration/test_release_gate_fail_closed.py'),
  Path('scripts/local_fault_injection.sh'), Path('scripts/local_load_soak.py'),
 ]
 assert all(p.exists() for p in required)


def test_local_git_provenance_has_real_clean_commit_and_immutable_tag():
 d=json.loads(Path('reports/LOCAL_SOURCE_PROVENANCE.json').read_text())
 assert re.fullmatch(r'[0-9a-f]{40}',d['git_commit_sha'])
 assert d['clean_tree'] is True
 assert d['immutable_tag_present'] is True
 assert any(__import__('re').fullmatch(r'v0\.3\.0-phase(?:29|[3-9]\d|\d{3,})(?:-local)?', t) for t in d['tags_at_head'])


def test_release_manifest_test_count_parser_supports_grouped_pytest_collection():
 from scripts.generate_release_manifest import test_count
 assert test_count() == __import__('scripts.generate_project_status', fromlist=['test_count']).test_count()
 assert test_count() is not None and test_count() >= 600
