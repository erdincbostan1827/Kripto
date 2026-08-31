import json
import tomllib
from pathlib import Path

import yaml

ROOT=Path(__file__).resolve().parents[2]


def test_canonical_profile_matches_backend_and_frontend_manifests():
    profile=yaml.safe_load((ROOT/'architecture_profile.yaml').read_text())
    pyproject=tomllib.loads((ROOT/'pyproject.toml').read_text())
    package=json.loads((ROOT/'frontend/package.json').read_text())
    assert profile['release']==pyproject['project']['version']==package['version']=='0.3.0'
    assert package['dependencies']['react']==profile['frontend']['react']
    assert package['dependencies']['@mui/material']==profile['frontend']['material_ui']
    assert package['dependencies']['@tanstack/react-query']==profile['frontend']['server_state'].split()[-1]
    assert package['dependencies']['lightweight-charts'].startswith('5.')
    assert package['devDependencies']['typescript']==profile['frontend']['typescript']
    assert package['devDependencies']['vite']==profile['frontend']['vite']


def test_typescript_strict_and_production_defaults_are_conservative():
    tsconfig=json.loads((ROOT/'frontend/tsconfig.json').read_text())
    assert tsconfig['compilerOptions']['strict'] is True
    env=(ROOT/'.env.example').read_text()
    assert 'MODE=PAPER' in env
    assert 'MARKET_TYPE=SPOT' in env
    assert 'LIVE_TRADING_ENABLED=false' in env
    assert 'AUTO_EXECUTION=false' in env


def test_gitignore_blocks_runtime_secrets_and_frontend_artifacts():
    text=(ROOT/'.gitignore').read_text()
    for required in ('.env','secrets/*','frontend/node_modules/','frontend/dist/'):
        assert required in text
