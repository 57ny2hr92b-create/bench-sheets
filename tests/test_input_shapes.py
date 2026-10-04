"""Malformed author input stays a field diagnostic at every public entry point."""
import copy
import json
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import build
from tools import schema


@pytest.mark.parametrize('field,value,path', [
    ('formula', None, 'formula'),
    ('formula', [], 'formula'),
    ('formula', {'rows': [None]}, 'formula.rows[0]'),
    ('formula', {'rows': 'flour'}, 'formula.rows'),
    ('method', {}, 'method'),
    ('method', [None], 'method[0]'),
    ('method', [{'head': ['Mix.'], 'text': 'Mix.'}], 'method[0].head'),
    ('revisions', [None], 'revisions[0]'),
    ('contains', 'Milk', 'contains'),
    ('contains', [None], 'contains[0]'),
    ('uses', [{}], 'uses[0]'),
    ('uses', None, 'uses'),
    ('kind', [], 'kind'),
    ('dense', 'false', 'dense'),
    ('figures', {'items': [None]}, 'figures.items[0]'),
    ('variants', {'items': [None]}, 'variants.items[0]'),
    ('variants', {'items': [{'name': 'A', 'rows': [None]}]}, 'variants.items[0].rows[0]'),
])
def test_malformed_card_fields_have_exact_paths_and_do_not_mutate(field, value, path):
    recs = build.load_recipes()
    r = recs['FR-003']
    r[field] = value
    before = copy.deepcopy(r)
    lint = schema.run(build.load_library(), recs, build.FIGS, quiet=True)
    assert any(d['path'] == path and d['rule'] == 'input.type' for d in lint.diagnostics)
    assert r == before


@pytest.mark.parametrize('field,value,path', [
    ('formula', {'parts': [None]}, 'formula.parts[0]'),
    ('formula', {'parts': [{'rows': []}], 'stages': 'Primo'}, 'formula.stages'),
    ('key_figures', [None], 'key_figures[0]'),
    ('pages', ['method'], 'pages[0]'),
    ('pages', [[None]], 'pages[0][0]'),
    ('done_when', [['Crumb']], 'done_when[0]'),
    ('schedule', [], 'schedule'),
])
def test_malformed_sheet_fields_have_exact_paths(field, value, path):
    recs = build.load_recipes()
    recs['CA-011'][field] = value
    lint = schema.run(build.load_library(), recs, build.FIGS, quiet=True)
    assert any(d['path'] == path and d['rule'] == 'input.type' for d in lint.diagnostics)


@pytest.mark.parametrize('flag', ['basis', 'carry', 'outside', 'dagger', 'approx'])
def test_row_flags_require_booleans(flag):
    recs = build.load_recipes()
    recs['FR-003']['formula']['rows'][0][flag] = 'false'
    lint = schema.run(build.load_library(), recs, build.FIGS, quiet=True)
    assert any(d['path'] == f'formula.rows[0].{flag}' and d['rule'] == 'input.type' for d in lint.diagnostics)


@pytest.mark.parametrize('token', ['method:abc', 'method:1-999999999', 'method:0', 'method:3-1', 'formula:1'])
def test_invalid_page_ranges_fail_without_expanding_them(token):
    recs = build.load_recipes()
    recs['CA-011']['pages'] = [['formula'], [token, 'done_when', 'revisions']]
    lint = schema.run(build.load_library(), recs, build.FIGS, quiet=True)
    assert any(d['path'] == 'pages[1][0]' and d['rule'] == 'pages.range' for d in lint.diagnostics)


@pytest.mark.parametrize('field,value,path', [('families', None, 'families'), ('families', [None], 'families[0]'), ('index', [], 'index')])
def test_library_shapes_are_diagnostics(field, value, path):
    lib = build.load_library()
    lib[field] = value
    lint = schema.run(lib, build.load_recipes(), build.FIGS, quiet=True)
    assert any(d['code'] == 'library' and d['path'] == path and d['rule'] == 'input.type' for d in lint.diagnostics)


def test_json_continues_after_malformed_recipe(monkeypatch, capsys):
    recs = build.load_recipes()
    recs['CA-011']['uses'] = [None]
    recs['FR-003']['formula']['rows'][0]['g'] = '113'
    monkeypatch.setattr(build, 'load_recipes', lambda: recs)
    with pytest.raises(SystemExit) as exc:
        build.lint(json_output=True)
    report = json.loads(capsys.readouterr().out)
    assert exc.value.code == 1 and report['report_version'] == 1
    assert any(d['code'] == 'CA-011' and d['path'] == 'uses[0]' for d in report['diagnostics'])
    assert any(d['code'] == 'FR-003' and d['rule'] == 'quantity.invalid' for d in report['diagnostics'])
    assert all(d['code'] != 'input' for d in report['diagnostics'])


def test_preview_malformed_uses_fails_cleanly(monkeypatch, capsys, tmp_path):
    recs = build.load_recipes()
    recs['FR-003']['uses'] = [None]
    monkeypatch.setattr(build, 'load_recipes', lambda: recs)
    monkeypatch.setattr(build, 'OUT', tmp_path)
    with pytest.raises(SystemExit, match='lint error'):
        build.preview('FR-003')
    assert 'uses[0]' in capsys.readouterr().out


def test_unknown_root_is_warning_but_row_typo_is_error():
    recs = build.load_recipes()
    recs['FR-003']['future_metadata'] = {'a': 1}
    recs['FR-003']['formula']['rows'][0]['gram'] = 113
    lint = schema.run(build.load_library(), recs, build.FIGS, quiet=True)
    assert any(d['path'] == 'future_metadata' and d['severity'] == 'warning' and d['rule'] == 'field.unknown' for d in lint.diagnostics)
    assert any(d['path'] == 'formula.rows[0].gram' and d['severity'] == 'error' and d['rule'] == 'field.unknown' for d in lint.diagnostics)


def test_zero_false_and_unknown_weights_keep_their_meaning():
    recs = build.load_recipes()
    row = recs['FR-003']['formula']['rows'][0]
    row.update(g=0, carry=False, approx=False)
    recs['FR-003']['formula']['rows'][1]['g'] = '—'
    assert not schema.run(build.load_library(), recs, build.FIGS, quiet=True).errors


@pytest.mark.parametrize('item', [{}, {'svg': 'missing.svg'}, {'gen': 'fold', 'svg': 'BR-023-fig1.svg'}, {'gen': 'dimensions', 'width': -1, 'height': 10}])
def test_figure_errors_identify_the_item(item):
    recs = build.load_recipes()
    recs['CA-011']['figures'] = {'items': [item]}
    lint = schema.run(build.load_library(), recs, build.FIGS, quiet=True)
    assert any(d['path'] == 'figures.items[0]' and d['rule'] == 'figure.invalid' for d in lint.diagnostics)


def test_legacy_null_notes_are_valid():
    recs = build.load_recipes()
    recs['BR-023']['method_rail'][0]['notes'] = None
    assert not schema.run(build.load_library(), recs, build.FIGS, quiet=True).errors


@pytest.mark.parametrize('change,path', [
    (lambda r: r['formula']['parts'].append({'name': 'Extra'}), 'formula.parts[1].rows'),
    (lambda r: r.update(figures={'title': 'Diagram'}), 'figures.items'),
    (lambda r: r['formula'].update(total='Total'), 'formula.total'),
    (lambda r: r['formula']['parts'][0].update(subtotal='Subtotal'), 'formula.parts[0].subtotal'),
])
def test_missing_or_malformed_render_containers_block_lint(change, path):
    recs = build.load_recipes()
    # Use one part so the appended missing-row part has a stable position.
    recs['CA-011']['formula']['parts'] = recs['CA-011']['formula']['parts'][:1]
    change(recs['CA-011'])
    lint = schema.run(build.load_library(), recs, build.FIGS, quiet=True)
    assert any(d['path'] == path and d['severity'] == 'error' for d in lint.diagnostics)


def test_mixed_unknown_variant_keys_do_not_abort_other_recipes():
    recs = build.load_recipes()
    recs['BR-024']['variants']['items'][0].update({1: 2, 'typo': 3})
    recs['FR-003']['formula']['rows'][0]['g'] = '113'
    lint = schema.run(build.load_library(), recs, build.FIGS, quiet=True)
    assert any(d['code'] == 'BR-024' and d['rule'] == 'field.unknown' for d in lint.diagnostics)
    assert any(d['code'] == 'FR-003' and d['rule'] == 'quantity.invalid' for d in lint.diagnostics)
