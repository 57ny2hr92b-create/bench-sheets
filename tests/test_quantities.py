"""Ingredient quantities must be safe inputs to the formula calculations."""
import copy
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import build
from tools import schema


def validate_change(code, change):
    recs = build.load_recipes()
    recipe = copy.deepcopy(recs[code])
    change(recipe)
    lint = schema.Lint()
    schema.lint_recipe(recipe, build.load_library(), recs, lint, build.FIGS)
    return lint


@pytest.mark.parametrize('value', [
    '750', '1.5', '2–3', '', 'pinch', None, True, False,
    -1, -0.5, float('nan'), float('inf'), float('-inf'), {}, [1],
])
def test_sheet_rejects_invalid_grams_with_location(value):
    def change(r):
        row = r['formula']['parts'][0]['rows'][1]
        row['g'] = value
        row['approx'] = True  # approximation never disables type checking
    lint = validate_change('CA-011', change)
    assert any('formula.parts[0].rows[1].g' in error for error in lint.errors)


@pytest.mark.parametrize('value', [0, 1, 0.5, '—'])
def test_sheet_accepts_numbers_and_unspecified_placeholder(value):
    lint = validate_change('CA-011', lambda r: r['formula']['parts'][0]['rows'][1].update(g=value))
    assert not lint.errors


def test_quoted_number_error_explains_how_to_fix_it():
    lint = validate_change('CA-011', lambda r: r['formula']['parts'][0]['rows'][1].update(g='750'))
    assert any('quotes' in error and '750' in error for error in lint.errors)


@pytest.mark.parametrize('code,path,change', [
    ('FR-003', 'formula.rows[0].g', lambda r: r['formula']['rows'][0].update(g='250')),
    ('BR-024', 'variants.items[0].rows[0].g', lambda r: r['variants']['items'][0]['rows'][0].update(g='120')),
    ('BR-023', 'formula.parts[0].rows[0].g[1]', lambda r: r['formula']['parts'][0]['rows'][0].update(g=[60, '175', 135])),
])
def test_card_variant_and_stage_quantities_are_checked(code, path, change):
    lint = validate_change(code, change)
    assert any(path in error for error in lint.errors)


@pytest.mark.parametrize('value', [750, '750', '—', [60, 175], [60, True, 135], [60, {}, 135], [60, [175], 135]])
def test_staged_formula_requires_one_valid_value_per_stage(value):
    lint = validate_change('BR-023', lambda r: r['formula']['parts'][0]['rows'][0].update(g=value))
    assert any('formula.parts[0].rows[0].g' in error for error in lint.errors)


def test_arrow_placeholder_requires_carried_row():
    lint = validate_change('BR-023', lambda r: r['formula']['parts'][0]['rows'][0].update(g=[60, '→', 135]))
    assert any('formula.parts[0].rows[0].g[1]' in error for error in lint.errors)


@pytest.mark.parametrize('carry', ['false', 'true', 1])
def test_arrow_requires_a_real_boolean_carry_flag(carry):
    lint = validate_change('BR-023', lambda r: r['formula']['parts'][0]['rows'][0].update(g=[60, '→', 135], carry=carry))
    assert any('formula.parts[0].rows[0].g[1]' in error for error in lint.errors)


def test_existing_stage_placeholders_and_carry_rows_still_pass():
    lint = validate_change('BR-023', lambda r: None)
    assert not lint.errors


def test_missing_grams_report_the_field_even_for_carry():
    def change(r):
        row = r['formula']['parts'][0]['rows'][0]
        row.pop('g')
        row['carry'] = True
    lint = validate_change('BR-023', change)
    assert any('formula.parts[0].rows[0].g' in error for error in lint.errors)
