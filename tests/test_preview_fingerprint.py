import copy
import pathlib
import shutil
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import build
from tools import preview


@pytest.fixture
def source(tmp_path):
    for name in ('build.py', 'requirements.txt', 'library.yaml'):
        shutil.copyfile(ROOT / name, tmp_path / name)
    for name in ('tools', 'templates', 'fonts', 'recipes'):
        shutil.copytree(ROOT / name, tmp_path / name)
    return tmp_path


@pytest.mark.parametrize('file', ['templates/card.html.j2', 'tools/fit.py', 'fonts/ibm-plex-sans-latin-400-normal.woff2', 'library.yaml'])
def test_renderer_or_library_edits_invalidate_preview(source, file):
    r = build.load_recipes()['FR-003']
    before = preview.fingerprint(source, r, {})
    path = source / file
    path.write_bytes(path.read_bytes() + b'\n')
    assert before['inputs_sha256'] != preview.fingerprint(source, r, {})['inputs_sha256']


def test_referenced_figures_and_components_invalidate_preview(source):
    recs = build.load_recipes()
    r = recs['BR-023']
    before = preview.fingerprint(source, r, {})
    path = source / 'recipes' / 'figures' / r['schedule']['svg']
    path.write_bytes(path.read_bytes() + b'\n')
    assert before['inputs_sha256'] != preview.fingerprint(source, r, {})['inputs_sha256']
    r = recs['CA-011']
    refs = {'FR-003': copy.deepcopy(recs['FR-003'])}
    before = preview.fingerprint(source, r, refs)
    refs['FR-003']['formula']['rows'][0]['g'] += 1
    assert before['inputs_sha256'] != preview.fingerprint(source, r, refs)['inputs_sha256']
