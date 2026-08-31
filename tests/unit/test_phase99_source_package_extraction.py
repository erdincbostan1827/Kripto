from __future__ import annotations

import os
import zipfile
from pathlib import Path

import pytest

from scripts.extract_source_package import extract


def test_extract_restores_unix_executable_mode(tmp_path: Path):
    package=tmp_path/'source.zip'
    info=zipfile.ZipInfo('project/install.sh')
    info.create_system=3
    info.external_attr=(0o100755 << 16)
    with zipfile.ZipFile(package,'w') as z:
        z.writestr(info,b'#!/bin/sh\n')
    out=tmp_path/'out'
    result=extract(package,out)
    target=out/'project/install.sh'
    assert target.is_file()
    assert target.stat().st_mode & 0o111
    assert 'project/install.sh' in result['executable_files_restored']


def test_extract_rejects_path_traversal(tmp_path: Path):
    package=tmp_path/'bad.zip'
    with zipfile.ZipFile(package,'w') as z:
        z.writestr('../escape.txt',b'x')
    with pytest.raises(ValueError):
        extract(package,tmp_path/'out')
    assert not (tmp_path/'escape.txt').exists()
