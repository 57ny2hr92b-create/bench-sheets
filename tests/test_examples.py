"""Frozen authoring examples protect arithmetic, page structure, and typography."""
import copy
import hashlib
import json
import pathlib
import sys

import pytest
import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import build
from tools import schema, fit

FIXTURES = ROOT / 'tests' / 'fixtures'


def examples():
    return {p.stem: yaml.safe_load(p.read_text()) for p in (FIXTURES / 'recipes').glob('*.yaml')}


def test_examples_keep_their_page_structure_and_printed_content(monkeypatch):
    recs = examples()
    lib = yaml.safe_load((FIXTURES / 'library.yaml').read_text())
    monkeypatch.setattr(build, 'FIGS', FIXTURES / 'recipes' / 'figures')
    lint = schema.run(lib, recs, build.FIGS)
    assert not lint.errors
    expected = json.loads((FIXTURES / 'artboard-sha256.json').read_text())
    actual = {}
    for recipe in recs.values():
        for name, html in build.render_recipe(build.env(), build.derive(recipe, recs)):
            actual[name] = hashlib.sha256(html.encode()).hexdigest()
    assert actual == expected, 'Printed output changed; review actual pages before updating the baseline.'


def test_examples_have_known_weights_and_percentages(monkeypatch):
    recs = examples()
    monkeypatch.setattr(build, 'FIGS', FIXTURES / 'recipes' / 'figures')
    staged = build.derive(copy.deepcopy(recs['BR-023']), recs)
    assert staged['formula']['total']['total_fmt'] == '1,221'
    variations = build.derive(copy.deepcopy(recs['BR-024']), recs)
    kalamata = next(v for v in variations['variants']['items'] if v['name'].startswith('Kalamata'))
    assert kalamata['g_fmt'] == '168'
    assert kalamata['pct_of_formula'] == '11.9'


def test_all_example_pages_fit_in_chromium(tmp_path, monkeypatch):
    monkeypatch.setattr(build, 'FIGS', FIXTURES / 'recipes' / 'figures')
    recs = examples()
    files = []
    for recipe in recs.values():
        for name, html in build.render_recipe(build.env(), build.derive(recipe, recs)):
            path = tmp_path / name
            path.write_text(html)
            files.append(path)
    assert fit.check(files) == 0
