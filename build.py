"""Bench Sheet build: recipes/*.yaml -> out/project/*.dc.html + index, PDFs and the site.

    python build.py build            render everything into out/
    python build.py check            render, then measure fit in Chromium (needs playwright + fonts)
    python build.py next-code CA     first free number in a family
    python build.py new CA "Name"    scaffold a recipe file with the next code
    python build.py lint             validate without rendering
"""
import sys, json, re, pathlib, datetime, argparse
import yaml
from jinja2 import Environment, FileSystemLoader, ChainableUndefined

ROOT = pathlib.Path(__file__).resolve().parent
RECIPES = ROOT / 'recipes'
FIGS = RECIPES / 'figures'
OUT = ROOT / 'out'
TEMPLATES = ROOT / 'templates'

LETTER = (816, 1056)
CARD = (768, 480)
TENT = (528, 816)


# ----------------------------------------------------------------------------- helpers

def fmt_g(v, approx=False):
    if v in ('—', '→', None, ''):
        return v or '—'
    if isinstance(v, str):
        return v
    s = f'{v:,.1f}'.rstrip('0').rstrip('.') if isinstance(v, float) else f'{v:,}'
    return ('≈ ' + s) if approx else s


def fmt_pct(x):
    if x is None: return '—'
    from decimal import Decimal, ROUND_HALF_UP
    return str(Decimal(str(x)).quantize(Decimal('0.1'), rounding=ROUND_HALF_UP))


def whole(x):
    from decimal import Decimal, ROUND_HALF_UP
    return int(Decimal(str(x)).quantize(Decimal('1'), rounding=ROUND_HALF_UP))


def stage_widths(stages):
    return [56 + 4 * (min(len(s), 6) - 4) for s in list(stages) + ['Total']]


def rev_num(rev):
    m = re.search(r'(\d+)', str(rev))
    return int(m.group(1)) if m else 0


# ----------------------------------------------------------------------------- formula math

def compute_formula(F):
    """Fill pct / g_fmt / totals in place. Basis = rows flagged basis: true."""
    stages = F.get('stages')
    parts = F['parts']

    def row_total(row):
        g = row['g']
        if stages:
            vals = [x for x in g if isinstance(x, (int, float))]
            if row.get('carry') or row.get('total') == '—':
                return None
            return sum(vals) if vals else None
        return g if isinstance(g, (int, float)) else None

    for p in parts:
        for row in p['rows']:
            row['_total'] = row_total(row)
    formula_basis = sum(r['_total'] for p in parts if not p.get('outside') for r in p['rows'] if r.get('basis') and r['_total'])
    for p in parts:
        part_basis = sum(r['_total'] for r in p['rows'] if r.get('basis') and r['_total']) or formula_basis
        p['_basis'] = part_basis
        for row in p['rows']:
            t = row['_total']
            if 'pct' in row:
                pass
            elif p.get('outside') or row.get('carry') or t is None or not part_basis:
                row['pct'] = '—'
            else:
                row['pct'] = fmt_pct(100 * t / part_basis)
            if stages:
                row['g_fmt'] = [fmt_g(x) for x in row['g']]
                row['total_fmt'] = fmt_g(t if t is not None else '—')
            else:
                row['g_fmt'] = fmt_g(row['g'], row.get('approx'))
        if p.get('subtotal') is not None:
            st = p['subtotal']
            tot = sum(r['_total'] for r in p['rows'] if r['_total'] is not None)
            st['g_fmt'] = fmt_g(whole(tot), any(r.get('approx') for r in p['rows']))
            st['pct'] = '—' if p.get('outside') or not part_basis else fmt_pct(100 * tot / part_basis)
    if F.get('total') is not None:
        T = F['total']
        rows = [r for p in parts if not p.get('outside') for r in p['rows']]
        grand = sum(r['_total'] for r in rows if r['_total'] is not None)
        T['pct'] = fmt_pct(100 * grand / formula_basis) if formula_basis else '—'
        T['divisor'] = f'{grand / formula_basis:.2f}' if formula_basis else '—'
        grand = whole(grand)
        if stages:
            cols = []
            for i in range(len(stages)):
                cols.append(sum(r['g'][i] for r in rows if isinstance(r['g'][i], (int, float))))
            T['g_fmt'] = [fmt_g(c) for c in cols]
            T['total_fmt'] = fmt_g(grand)
        else:
            T['g_fmt'] = fmt_g(grand)
    F['_basis'] = formula_basis
    F['_grand'] = sum(r['_total'] for p in parts if not p.get('outside') for r in p['rows'] if r['_total'] is not None)
    return F


def compute_variants(V, F):
    """Variants are named sub-formulas laid over the main formula (toppings, inclusions, finishes).
    Each variant's total prints as a % of the main formula's total (the dough weight); its rows
    print their own internal % so one multiplier scales the whole sheet."""
    grand = F.get('_grand') or 0
    for v in V.get('items', []):
        tot = sum(r['g'] for r in v['rows'] if isinstance(r['g'], (int, float)))
        v['g_fmt'] = fmt_g(whole(tot)) if tot else '—'
        v['pct_of_formula'] = fmt_pct(100 * tot / grand) if grand and tot else '—'
        for r in v['rows']:
            g = r['g']
            r['g_fmt'] = fmt_g(g, r.get('approx'))
            r['pct'] = fmt_pct(100 * g / tot) if isinstance(g, (int, float)) and tot else '—'
    return V


# ----------------------------------------------------------------------------- loading

STATUSES = ('draft', 'trial', 'standard', 'retired')


def live(recs):
    """Recipes that go on the site and in the index: trial + standard. Drafts render to out/drafts/
    for review; retired sheets stay in the repo as the record but are not rendered."""
    return {c: r for c, r in recs.items() if r.get('status', 'standard') in ('trial', 'standard')}


def load_library():
    return yaml.safe_load((ROOT / 'library.yaml').read_text())


def load_recipes():
    recs = {}
    for f in sorted(RECIPES.glob('*.yaml')):
        r = yaml.safe_load(f.read_text())
        r['_file'] = f.name
        if r['code'] in recs:
            raise SystemExit(f'duplicate code {r["code"]} in {f.name} and {recs[r["code"]]["_file"]}')
        recs[r['code']] = r
    return recs


def uses_of(r):
    """Codes this recipe cites: explicit `uses:` plus any XX-000 in formula rows, components or variant rows."""
    found = set(r.get('uses', []))
    pat = re.compile(r'\b([A-Z]{2}-\d{3})\b')
    def scan(obj):
        if isinstance(obj, str):
            found.update(pat.findall(obj))
        elif isinstance(obj, dict):
            for k, v in obj.items():
                if k in ('lede', 'notes', 'text', 'source', 'steps'):
                    continue  # prose mentions don't count
                scan(v)
        elif isinstance(obj, list):
            for v in obj: scan(v)
    scan(r.get('formula', {})); scan(r.get('components', {})); scan(r.get('variants', {}))
    found.discard(r['code'])
    return sorted(found)


def derive(r, recs):
    kind = r.get('kind', 'sheet')
    revs = r.get('revisions') or []
    last = revs[-1]
    r['rev'] = last['rev'] if str(last['rev']).startswith('Rev') else f'Rev {int(last["rev"]):02d}'
    r['date'] = last.get('date') or '—'
    r.setdefault('last_change', f'{r["rev"]} · {last["change"]}')
    r['_revnum'] = rev_num(r['rev'])
    r['_uses'] = uses_of(r)
    if 'formula' in r and kind != 'card':
        compute_formula(r['formula'])
        if r.get('variants'):
            compute_variants(r['variants'], r['formula'])
    if kind == 'card':
        # card formula: single flat part
        F = dict(parts=[dict(id='', name='', rows=r['formula']['rows'])],
                 total=dict(label=r['formula'].get('total', 'Total')))
        compute_formula(F)
        r['formula']['total'] = F['total']
    # method
    if kind == 'sheet':
        for i, s in enumerate(r.get('method', []), 1):
            s['n'] = i
            if s.get('target_f') and '→' in str(s.get('target', '')):
                s['target_f_line'] = True
        for s in r.get('schedule', {}) and [r['schedule']] or []:
            if s.get('svg'):
                s['svg'] = (FIGS / s['svg']).read_text()
        if r.get('figures'):
            from tools import figures as figgen
            for it in r['figures']['items']:
                it['svg'] = figgen.render(it) if it.get('gen') else (FIGS / it['svg']).read_text()
        r['_pages'] = plan_pages(r)
        r.setdefault('foot', default_foot(r))
    return r


SECTION_LABELS = dict(schedule='schedule', method='method', trials='trials', figures='figures',
                      done_when='done when', fixes='fixes', revisions='revisions', batch_log='batch log',
                      components='components', variants='variants')


def plan_pages(r):
    spec = r.get('pages') or [['formula'], ['method', 'done_when', 'trials', 'revisions']]
    pages = []
    rails = list(r.get('method_rail') or [])
    mi = 0
    for n, entry in enumerate(spec, 1):
        gap = 16 if n > 1 or r.get('dense') else 20
        names = entry
        if isinstance(entry, dict):
            names = entry['sections']; gap = entry.get('gap', gap)
        secs = []
        for name in names:
            if name.startswith('method'):
                m = re.match(r'method(?::(\d+)-(\d+))?', name)
                steps = r['method']
                if m.group(1):
                    a, b = int(m.group(1)), int(m.group(2))
                    steps = [s for s in steps if a <= s['n'] <= b]
                rail = rails[mi] if mi < len(rails) else {}
                mi += 1
                secs.append(dict(type='method', title=rail.get('title', 'Method'), sub=rail.get('sub') or 'Tick each step as done', notes=rail.get('notes'), steps=steps))
            elif name == 'figures':
                secs.append(dict(type='figures', items=r['figures']['items']))
            else:
                secs.append(dict(type=name))
        pages.append(dict(n=n, total=len(spec), gap=gap, sections=secs))
    return pages


def default_foot(r):
    names = []
    for pg in r['_pages'][1:]:
        for s in pg['sections']:
            lab = SECTION_LABELS.get(s['type'], s['type'])
            if s['type'] == 'figures':
                lab = r['figures'].get('title', 'figures').lower()
            if lab not in names: names.append(lab)
    return ', '.join(names)


# ----------------------------------------------------------------------------- codes

def next_code(recs, family):
    used = sorted(int(c.split('-')[1]) for c in recs if c.startswith(family + '-'))
    return f'{family}-{(used[-1] + 1) if used else 1:03d}'


# ----------------------------------------------------------------------------- rendering

def env():
    e = Environment(loader=FileSystemLoader(str(TEMPLATES)), undefined=ChainableUndefined, autoescape=False,
                    trim_blocks=False, lstrip_blocks=False)
    e.globals['stage_widths'] = stage_widths
    return e


def render_recipe(e, r):
    """[(filename, html)] for every artboard of one recipe."""
    out = []
    for fn, title, w, h in artboard_files(r):
        tpl = 'card.html.j2' if r.get('kind') == 'card' else ('tent.html.j2' if fn.endswith('-tent.dc.html') else 'sheet_page.html.j2')
        ctx = dict(r=r)
        if tpl == 'sheet_page.html.j2':
            ctx['page'] = r['_pages'][int(fn.rsplit('-', 1)[1].split('.')[0]) - 1]
        out.append((fn, e.get_template(tpl).render(**ctx)))
    return out


def artboard_files(r):
    """(filename, title, w, h) for every artboard a recipe produces."""
    out = []
    if r.get('kind', 'sheet') == 'card':
        out.append((f'{r["code"]}.dc.html', f'{r["code"]} card', *CARD))
    else:
        for pg in r['_pages']:
            out.append((f'{r["code"]}-{pg["n"]}.dc.html', f'{r["code"]} {r["name"].lower()} · page {pg["n"]}', *LETTER))
        if r.get('tent'):
            out.append((f'{r["code"]}-tent.dc.html', f'{r["code"]} tent card', *TENT))
    return out


def index_entries(recs, lib):
    recs = live(recs)
    fams = {}
    used_by = {}
    for r in recs.values():
        for u in r['_uses']:
            used_by.setdefault(u, set()).add(r['code'])
    for r in recs.values():
        fam = r['code'].split('-')[0]
        kind = r.get('kind', 'sheet')
        if kind == 'card':
            fmt, pp = 'Card', '1'
        else:
            n = len(r['_pages'])
            fmt = 'Assembly' if 'components' in r else 'Sheet'
            if r.get('tent'):
                fmt, pp = fmt + ' + tent', f'{n} + 1'
            else:
                pp = str(n)
        linked = sorted(set(r['_uses']) | used_by.get(r['code'], set()))
        if r.get('status') == 'trial': fmt += ' · trial'
        fams.setdefault(fam, []).append(dict(code=r['code'], name=r['name'], format=fmt, pages=pp, rev=r['_revnum'],
                                            linked=' · '.join(linked), contains=' · '.join(r['contains'])))
    order = [f['code'] for f in lib['families']]
    names = {f['code']: f['name'] for f in lib['families']}
    out = []
    for code in order:
        if code in fams:
            out.append(dict(code=code, name=names[code], entries=sorted(fams[code], key=lambda e: e['code'])))
    for code in fams:
        if code not in order:
            raise SystemExit(f'family {code} is not in library.yaml')
    return out


def paginate_index(families, blank_rows):
    """Rows per page: 21 data-ish rows fit under the title. Split families across pages if needed."""
    # weights: family header 32px, entry 27px; budget ~ 560px on page 1 (title+lede), ~ 730 on later pages
    pages, cur, h, budget = [], [], 0, 560
    for fam in families:
        fh = 32 + 27 * len(fam['entries'])
        if cur and h + fh > budget:
            pages.append(cur); cur, h, budget = [], 0, 730
        cur.append(fam); h += fh
    pages.append(cur)
    out = []
    for i, fams in enumerate(pages, 1):
        blanks = 0
        if i == len(pages):
            room = (560 if i == 1 else 730) - sum(32 + 27 * len(f['entries']) for f in fams) - 32
            blanks = max(0, min(blank_rows, room // 27))
        out.append(dict(n=i, total=len(pages), families=fams, blank_rows=blanks))
    return out


def build(check_only=False):
    lib = load_library()
    recs = load_recipes()
    from tools import schema
    L = schema.run(lib, recs, FIGS)
    # a half-written draft never blocks the build: its errors are reported and it is left out
    draft_codes = {c for c, r in recs.items() if r.get('status') == 'draft'}
    blocking = [e for e in L.errors if e.split(':')[0] not in draft_codes]
    broken_drafts = {e.split(':')[0] for e in L.errors if e.split(':')[0] in draft_codes}
    for c in sorted(broken_drafts): print(f'  (draft {c} has lint errors and is skipped)')
    if blocking:
        raise SystemExit(f'{len(blocking)} lint error(s); nothing rendered')
    for c in broken_drafts: recs.pop(c)
    retired = [c for c, r in recs.items() if r.get('status') == 'retired']
    for c in retired: recs.pop(c)
    for r in recs.values():
        derive(r, recs)
    for r in recs.values():
        for u in r['_uses']:
            if u not in recs:
                raise SystemExit(f'{r["code"]} cites {u}, which does not exist')
    if check_only:
        print(f'{len(recs)} recipes OK'); return
    e = env()
    proj = OUT / 'project'
    proj.mkdir(parents=True, exist_ok=True)
    for old in proj.glob('*.dc.html'): old.unlink()
    order = []
    # index
    idx_pages = paginate_index(index_entries(recs, lib), lib['index'].get('blank_rows', 6))
    for pg in idx_pages:
        fn = 'Index.dc.html' if pg['n'] == 1 else f'Index-{pg["n"]}.dc.html'
        (proj / fn).write_text(e.get_template('index.html.j2').render(lib=lib, page=pg))
        order.append(fn)
    # drafts: rendered for review only
    drafts = OUT / 'drafts'
    for old in drafts.glob('*.dc.html'): old.unlink()
    for r in recs.values():
        if r.get('status') == 'draft':
            drafts.mkdir(exist_ok=True)
            for fn, html in render_recipe(e, r): (drafts / fn).write_text(html)
    # live sheets, in code order
    for r in sorted(live(recs).values(), key=lambda r: r['code']):
        rendered = dict(render_recipe(e, r))
        for fn, title, w, h in artboard_files(r):
            (proj / fn).write_text(rendered[fn])
            order.append(fn)
    (OUT / 'manifest.json').write_text(json.dumps(dict(artboards=order, recipes=sorted(recs)), indent=1))
    print(f'rendered {len(order)} artboards from {len(recs)} recipes into {proj}')
    return order


def pdf(codes):
    """out/pdf/<CODE>.pdf per recipe (pages of a sheet in one file; tent and cards at their own size).
    Renders from the last build, so run `build` first. Drafts come from out/drafts/."""
    import re
    from playwright.sync_api import sync_playwright
    from tools import fit
    faces = fit.font_css()
    recs = load_recipes()
    codes = [c.upper() for c in codes] or sorted(live(recs))
    (OUT / 'pdf').mkdir(parents=True, exist_ok=True)
    written = []
    with sync_playwright() as pw:
        b = pw.chromium.launch(); pg = b.new_page()
        for code in codes:
            r = recs.get(code)
            if not r: raise SystemExit(f'no recipe {code}')
            src_dir = OUT / ('drafts' if r.get('status') == 'draft' else 'project')
            groups = {code: [], f'{code}-tent': []}
            for f in sorted(src_dir.glob(f'{code}*.dc.html')):
                (groups[f'{code}-tent'] if f.name.endswith('-tent.dc.html') else groups[code]).append(f)
            for name, files in groups.items():
                if not files: continue
                pages = []
                for f in files:
                    src = f.read_text()
                    inner = re.search(r'</helmet>\s*(.*?)\s*</x-dc>', src, re.S).group(1)
                    w, h = map(int, re.search(r'"\$preview":\{"width":(\d+),"height":(\d+)', src).groups())
                    pages.append(inner)
                # Always print on Letter. A Letter sheet fills the page; a card or tent card sits centred
                # with hairline crop marks, so it lands the same place on every printer.
                W, H = LETTER
                if (w, h) == LETTER:
                    css = f"@page{{size:8.5in 11in;margin:0}}body{{margin:0}}.pg{{width:{w}px;height:{h}px;page-break-after:always;overflow:hidden}}"
                    body = ''.join(f'<div class="pg">{p}</div>' for p in pages)
                else:
                    x, y = (W - w) // 2, (H - h) // 2
                    marks = ''.join(f'<i style="position:absolute;left:{mx}px;top:{my}px;width:{mw}px;height:{mh}px;background:#000"></i>'
                                    for (mx, my, mw, mh) in [
                                        (x - 20, y, 14, 1), (x, y - 20, 1, 14), (x + w + 6, y, 14, 1), (x + w, y - 20, 1, 14),
                                        (x - 20, y + h, 14, 1), (x, y + h + 6, 1, 14), (x + w + 6, y + h, 14, 1), (x + w, y + h + 6, 1, 14)])
                    css = (f"@page{{size:8.5in 11in;margin:0}}body{{margin:0}}.pg{{position:relative;width:{W}px;height:{H}px;page-break-after:always;overflow:hidden}}"
                           f".art{{position:absolute;left:{x}px;top:{y}px;width:{w}px;height:{h}px;overflow:hidden}}")
                    body = ''.join(f'<div class="pg"><div class="art">{p}</div>{marks}</div>' for p in pages)
                html = f"<!doctype html><html><head><meta charset='utf-8'><style>{faces}{css}</style></head><body>{body}</body></html>"
                tmp = OUT / '_pdf.html'; tmp.write_text(html)
                pg.goto('file://' + str(tmp)); pg.wait_for_timeout(300)
                out = OUT / 'pdf' / f'{name}.pdf'
                pg.pdf(path=str(out), width='8.5in', height='11in', print_background=True, prefer_css_page_size=True)
                written.append(out)
        b.close()
    (OUT / '_pdf.html').unlink(missing_ok=True)
    for o in written: print('wrote', o.relative_to(ROOT))
    return written


def inner_html(doc):
    """The artboard's inner <div> from a rendered .dc.html document."""
    return re.search(r'</helmet>\s*(.*?)\s*</x-dc>', doc, re.S).group(1)


def site():
    """out/site/: a static binder for GitHub Pages. index.html (the IX-00 pages, code and name linked, plus a
    Drafts list under them), <CODE>.html per recipe (its sheet pages, or the card), <CODE>-tent.html, and
    pdf/<CODE>.pdf. Drafts get pages and PDFs too, marked "draft", so nothing in the repo is invisible;
    they stay off the printed IX-00. Renders from recipes directly, so run after `build` (which lints) —
    `site` does both."""
    order = build()
    lib = load_library(); allrecs = load_recipes()
    recs = live(allrecs)
    drafts = {c: r for c, r in allrecs.items() if r.get('status') == 'draft' and c not in _broken_drafts(lib, allrecs)}
    for r in recs.values(): derive(r, recs)
    for r in drafts.values(): derive(r, {**recs, **drafts})
    e = env()
    out = OUT / 'site'
    if out.exists():
        import shutil; shutil.rmtree(out)
    out.mkdir(parents=True)
    tpl = e.get_template('site_page.html.j2')
    # index
    idx_pages = paginate_index(index_entries(recs, lib), lib['index'].get('blank_rows', 6))
    boards = [dict(w=LETTER[0], h=LETTER[1], html=inner_html(e.get_template('index.html.j2').render(lib=lib, page=pg, site=True))) for pg in idx_pages]
    draft_rows = [dict(code=c, name=r['name'], kind='Card' if r.get('kind') == 'card' else 'Sheet', rev=r['rev'], date=r['date'])
                  for c, r in sorted(drafts.items())]
    (out / 'index.html').write_text(tpl.render(title=lib['title'], boards=boards, page_size='8.5in 11in', pdf=None, code=None, name=None, drafts=draft_rows))
    # recipes
    pdfs = pdf(list(recs) + list(drafts))
    (out / 'pdf').mkdir()
    for pth in pdfs: (out / 'pdf' / pth.name).write_bytes(pth.read_bytes())
    for code, r in {**recs, **drafts}.items():
        rendered = render_recipe(e, r)
        sheets = [(fn, html) for fn, html in rendered if not fn.endswith('-tent.dc.html')]
        tents = [(fn, html) for fn, html in rendered if fn.endswith('-tent.dc.html')]
        w, h = CARD if r.get('kind') == 'card' else LETTER
        status = r.get('status', 'standard')
        boards = [dict(w=w, h=h, html=inner_html(html)) for fn, html in sheets]
        (out / f'{code}.html').write_text(tpl.render(title=f'{code} {r["name"]}', code=code, name=r['name'], boards=boards,
                                                     page_size=f'{w / 96}in {h / 96}in', pdf=f'pdf/{code}.pdf',
                                                     tent=f'{code}-tent.html' if tents else None, status=status))
        if tents:
            boards = [dict(w=TENT[0], h=TENT[1], html=inner_html(html)) for fn, html in tents]
            (out / f'{code}-tent.html').write_text(tpl.render(title=f'{code} tent card', code=code, name=r['name'] + ' · tent card', boards=boards,
                                                              page_size=f'{TENT[0] / 96}in {TENT[1] / 96}in', pdf=f'pdf/{code}-tent.pdf', status=status))
    import shutil as _sh; _sh.copytree(ROOT / 'fonts', out / 'fonts')
    (out / '.nojekyll').write_text('')
    print(f'site: {len(recs)} recipes, {len(drafts)} drafts, {len(pdfs)} pdfs in {out}')


def _broken_drafts(lib, recs):
    """Draft codes with lint errors; build() skips them, so the site must too."""
    from tools import schema
    import io, contextlib
    with contextlib.redirect_stdout(io.StringIO()):
        L = schema.run(lib, recs, FIGS)
    return {e.split(':')[0] for e in L.errors if recs.get(e.split(':')[0], {}).get('status') == 'draft'}


def scaffold(family, name, recs):
    code = next_code(recs, family)
    today = datetime.date.today().isoformat()
    doc = f'''code: {code}
kind: sheet
status: draft            # draft -> trial -> standard (-> retired); only trial and standard reach the site
name: {name}
cls: {dict(BR='Bread', PA='Pastry', CA='Cake', CK='Cookie', CF='Confection', CR='Cream & custard', FR='Frosting', GA='Ganache', SV='Savory').get(family, family)} ·
lede:
source:
contains: [Wheat]
equipment: []
key_figures:
- {{label: Yield, value: ''}}
- {{label: '', value: ''}}
- {{label: '', value: ''}}
- {{label: Plan, value: ''}}
- {{label: Oven · 350 °F, value: 175 °C}}
formula:
  basis: '% · flour = 100'
  notes:
  - † Doesn't scale in a straight line past 2×.
  parts:
  - id: A
    name:
    rows:
    - {{name: All-purpose flour, g: 0, basis: true}}
method:
- {{head: Prep., text: '', time: '—', target: 175 °C, target_f: 350 °F}}
done_when: [[Top, '']]
keeps: [[Room temp, '']]
trials:
  sub: Change one variable per trial
  columns: [Trial A, Trial B, Trial C]
  rows:
  - {{var: Date, values: ['', '', '']}}
  - {{var: Change, values: [As written, '', '']}}
  - {{var: Staff rating 1–5, values: ['', '', '']}}
revisions:
- {{rev: Rev 01, date: '{today}', change: First issue, source: —}}
pages:
- [formula]
- [method, done_when, trials, revisions]
'''
    path = RECIPES / f'{code}.yaml'
    path.write_text(doc)
    print(f'wrote {path}')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('cmd', choices=['build', 'check', 'lint', 'list', 'next-code', 'new', 'pdf', 'site'])
    ap.add_argument('args', nargs='*')
    a = ap.parse_args()
    if a.cmd == 'lint':
        build(check_only=True)
    elif a.cmd == 'build':
        build()
    elif a.cmd == 'check':
        build()
        from tools import fit
        shots = OUT / 'shots'; shots.mkdir(exist_ok=True)
        if fit.check(sorted((OUT / 'project').glob('*.dc.html')), screenshots=shots):
            raise SystemExit(1)
    elif a.cmd == 'pdf':
        build(); pdf(a.args)
    elif a.cmd == 'site':
        site()
    elif a.cmd == 'list':
        for c, r in sorted(load_recipes().items()):
            print(f"{c}  {r.get('status', 'standard'):9s} {r.get('kind', 'sheet'):6s} {r['name']}")
    elif a.cmd == 'next-code':
        print(next_code(load_recipes(), a.args[0].upper()))
    elif a.cmd == 'new':
        scaffold(a.args[0].upper(), ' '.join(a.args[1:]) or 'Untitled', load_recipes())


if __name__ == '__main__':
    main()
