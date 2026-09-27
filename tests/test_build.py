"""Regression tests. Run: python -m pytest -q
The fit test needs Playwright + Chromium (pip install playwright; playwright install chromium)."""
import json, pathlib, subprocess, sys, pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import build  # noqa: E402


@pytest.fixture(scope='session')
def built():
    order = build.build()
    return order


def test_lint_clean():
    from tools import schema
    lib, recs = build.load_library(), build.load_recipes()
    L = schema.run(lib, recs, build.FIGS)
    assert not L.errors


def test_percent_math():
    F = dict(parts=[dict(id='A', rows=[dict(name='Flour', g=200, basis=True), dict(name='Water', g=150), dict(name='Salt', g=1.25)])], total=dict(label='Total'))
    build.compute_formula(F)
    rows = F['parts'][0]['rows']
    assert [r['pct'] for r in rows] == ['100.0', '75.0', '0.6']   # 0.625 % -> 0.6 (ROUND_HALF_UP at one decimal)
    assert F['total']['g_fmt'] == '351'


def test_stage_grid_totals():
    recs = build.load_recipes()
    r = build.derive(recs['BR-023'], recs)
    F = r['formula']
    flour = next(row for row in F['parts'][0]['rows'] if row['name'].startswith('Bread flour'))
    assert flour['_total'] == 370 and flour['pct'] == '100.0'
    assert F['total']['g_fmt'][-1] == '1,221'


def test_every_recipe_renders(built):
    proj = ROOT / 'out' / 'project'
    assert (proj / 'Index.dc.html').exists() and (proj / 'canvas.json').exists()
    canvas = json.loads((proj / 'canvas.json').read_text())
    assert set(canvas['order']) == set(built)
    assert all(b in canvas['boards'] for b in built)
    for fn in built:
        assert (proj / fn).exists(), fn


def test_index_links_are_symmetric(built):
    recs = build.load_recipes()
    for r in recs.values(): build.derive(r, recs)
    entries = {e['code']: e for fam in build.index_entries(recs, build.load_library()) for e in fam['entries']}
    assert 'CR-001' in entries['PA-004']['linked'] and 'PA-004' in entries['CR-001']['linked']


def test_next_code():
    recs = build.load_recipes()
    assert build.next_code(recs, 'BR') == 'BR-025'
    assert build.next_code(recs, 'GA') == 'GA-001'


@pytest.mark.skipif(not (ROOT / 'fonts').exists(), reason='fonts/ missing')
def test_everything_fits(built):
    pytest.importorskip('playwright')
    from tools import fit
    assert fit.check(sorted((ROOT / 'out' / 'project').glob('*.dc.html'))) == 0


def test_status_gates_canvas(tmp_path, monkeypatch):
    """A draft renders to out/drafts only; a retired recipe is not rendered; neither is indexed."""
    import shutil, yaml
    src = ROOT / 'recipes' / 'FR-003.yaml'
    d = yaml.safe_load(src.read_text()); d['code'] = 'FR-999'; d['status'] = 'draft'
    r = yaml.safe_load(src.read_text()); r['code'] = 'FR-998'; r['status'] = 'retired'
    (ROOT / 'recipes' / 'FR-999.yaml').write_text(yaml.safe_dump(d, allow_unicode=True))
    (ROOT / 'recipes' / 'FR-998.yaml').write_text(yaml.safe_dump(r, allow_unicode=True))
    try:
        order = build.build()
        assert 'FR-999.dc.html' not in order and 'FR-998.dc.html' not in order
        assert (ROOT / 'out' / 'drafts' / 'FR-999.dc.html').exists()
        idx = (ROOT / 'out' / 'project' / 'Index.dc.html').read_text()
        assert 'FR-999' not in idx and 'FR-998' not in idx
    finally:
        (ROOT / 'recipes' / 'FR-999.yaml').unlink(); (ROOT / 'recipes' / 'FR-998.yaml').unlink()
        build.build()


def test_site_builds(built):
    pytest.importorskip('playwright')
    if not (ROOT / 'fonts').exists(): pytest.skip('fonts')
    build.site()
    site = ROOT / 'out' / 'site'
    idx = (site / 'index.html').read_text()
    for code in build.live(build.load_recipes()):
        assert (site / f'{code}.html').exists() and (site / 'pdf' / f'{code}.pdf').exists(), code
        assert f'href="{code}.html"' in idx
    assert (site / 'CK-002-tent.html').exists()


def test_variants_math_and_lint():
    """Variants: each item's total prints as % of the dough; rows print their internal %."""
    recs = build.load_recipes()
    r = build.derive(recs['BR-024'], recs)
    kal = next(v for v in r['variants']['items'] if v['name'].startswith('Kalamata'))
    assert kal['g_fmt'] == '168' and kal['pct_of_formula'] == '11.9'          # 168 / 1411
    assert [row['pct'] for row in kal['rows']] == ['71.4', '23.8', '3.6', '1.2']
    assert any(s['type'] == 'variants' for pg in r['_pages'] for s in pg['sections'])
    from tools import schema
    import copy
    bad = copy.deepcopy(build.load_recipes()['BR-024'])
    bad['variants']['items'][0]['topping'] = 'stray'
    del bad['variants']['items'][1]['rows']
    L = schema.Lint(); schema.lint_recipe(bad, build.load_library(), recs, L, build.FIGS)
    assert any('unknown keys' in e for e in L.errors) and any('no rows' in e for e in L.errors)
