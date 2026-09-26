"""Bench Sheet build: recipes/*.yaml -> out/project/*.dc.html + canvas.json + index.

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
ROW_GAP = 120
COL_GAP = 80


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
    return F


# ----------------------------------------------------------------------------- loading

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
    """Codes this recipe cites: explicit `uses:` plus any XX-000 in formula rows or components."""
    found = set(r.get('uses', []))
    pat = re.compile(r'\b([A-Z]{2}-\d{3})\b')
    def scan(obj):
        if isinstance(obj, str):
            found.update(pat.findall(obj))
        elif isinstance(obj, dict):
            for k, v in obj.items():
                if k in ('lede', 'notes', 'text', 'source'):
                    continue  # prose mentions don't count
                scan(v)
        elif isinstance(obj, list):
            for v in obj: scan(v)
    scan(r.get('formula', {})); scan(r.get('components', {}))
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
            for it in r['figures']['items']:
                it['svg'] = (FIGS / it['svg']).read_text()
        r['_pages'] = plan_pages(r)
        r.setdefault('foot', default_foot(r))
    return r


SECTION_LABELS = dict(schedule='schedule', method='method', trials='trials', figures='figures',
                      done_when='done when', fixes='fixes', revisions='revisions', batch_log='batch log',
                      components='components')


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
    # weights: family header 32px, entry 27px; budget ~ 640px on page 1 (title+lede), ~ 730 on later pages
    pages, cur, h, budget = [], [], 0, 640
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
            room = (640 if i == 1 else 730) - sum(32 + 27 * len(f['entries']) for f in fams) - 32
            blanks = max(0, min(blank_rows, room // 27))
        out.append(dict(n=i, total=len(pages), families=fams, blank_rows=blanks))
    return out


def build(check_only=False):
    lib = load_library()
    recs = load_recipes()
    from tools import schema
    L = schema.run(lib, recs, FIGS)
    if L.errors:
        raise SystemExit(f'{len(L.errors)} lint error(s); nothing rendered')
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
    boards, order, pages = {}, [], []
    # index
    idx_pages = paginate_index(index_entries(recs, lib), lib['index'].get('blank_rows', 6))
    for pg in idx_pages:
        fn = 'Index.dc.html' if pg['n'] == 1 else f'Index-{pg["n"]}.dc.html'
        (proj / fn).write_text(e.get_template('index.html.j2').render(lib=lib, page=pg))
        boards[fn] = dict(x=(pg['n'] - 1) * (LETTER[0] + COL_GAP), y=0, w=LETTER[0], h=LETTER[1], title=f'IX-00 library index · page {pg["n"]}', paper='letter')
        order.append(fn)
    # one canvas page per family
    fam_names = {f['code']: f['name'] for f in lib['families']}
    by_fam = {}
    for r in recs.values():
        by_fam.setdefault(r['code'].split('-')[0], []).append(r)
    for fam in [f['code'] for f in lib['families']]:
        if fam not in by_fam: continue
        pages.append(dict(id=fam.lower(), name=f'{fam} · {fam_names[fam]}'))
        y = 0
        for r in sorted(by_fam[fam], key=lambda r: r['code']):
            x = 0; row_h = 0
            for fn, title, w, h in artboard_files(r):
                tpl = 'card.html.j2' if r.get('kind') == 'card' else ('tent.html.j2' if fn.endswith('-tent.dc.html') else 'sheet_page.html.j2')
                ctx = dict(r=r)
                if tpl == 'sheet_page.html.j2':
                    ctx['page'] = r['_pages'][int(fn.rsplit('-', 1)[1].split('.')[0]) - 1]
                (proj / fn).write_text(e.get_template(tpl).render(**ctx))
                boards[fn] = dict(x=x, y=y, w=w, h=h, title=title, page=fam.lower())
                if h == LETTER[1]: boards[fn]['paper'] = 'letter'
                order.append(fn)
                x += w + COL_GAP; row_h = max(row_h, h)
            y += row_h + ROW_GAP
    canvas = dict(v=3, createdOnFiles=lib['canvas'].get('createdOnFiles', {'v': 1, 'at': datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}),
                  title=lib['canvas']['title'], launch={'view': 'canvas'}, pages=pages, boards=boards, order=order, notes={},
                  designSystems=lib['canvas'].get('designSystems', []))
    (proj / 'canvas.json').write_text(json.dumps(canvas, ensure_ascii=False, separators=(',', ':')))
    (OUT / 'manifest.json').write_text(json.dumps(dict(artboards=order, recipes=sorted(recs)), indent=1))
    write_publish_plan(order)
    print(f'rendered {len(order)} artboards from {len(recs)} recipes into {proj}')
    return order


def write_publish_plan(order):
    """out/publish.json: the `files` map for the Artifact publish, including `null` removals for any
    artboard that published.yaml says is on the canvas but this build no longer produces."""
    pub_file = ROOT / 'published.yaml'
    published = yaml.safe_load(pub_file.read_text()) if pub_file.exists() else {}
    on_canvas = set(published.get('artboards') or [])
    files = {f'project/{fn}': f'project/{fn}' for fn in order if fn != 'Index.dc.html'}  # the index is file_path
    files['project/canvas.json'] = 'project/canvas.json'
    for fn in sorted(on_canvas - set(order)):
        files[f'project/{fn}'] = None
    plan = dict(url=published.get('url'), root='out', file_path='out/project/Index.dc.html', files=files,
                note='After a successful publish, run: python build.py published  (records this build as what is on the canvas)')
    (OUT / 'publish.json').write_text(json.dumps(plan, indent=1, ensure_ascii=False))


def record_published():
    manifest = json.loads((OUT / 'manifest.json').read_text())
    lib = load_library()
    pub_file = ROOT / 'published.yaml'
    prev = yaml.safe_load(pub_file.read_text()) if pub_file.exists() else {}
    doc = dict(url=lib['canvas']['url'], at=datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
               index_rev=lib['index']['rev'], artboards=manifest['artboards'])
    pub_file.write_text('# What the Test Kitchen canvas currently holds. Written by `python build.py published`; do not edit by hand.\n'
                        + yaml.safe_dump(doc, sort_keys=False, allow_unicode=True))
    gone = sorted(set(prev.get('artboards') or []) - set(manifest['artboards']))
    print(f'recorded {len(manifest["artboards"])} artboards as published' + (f'; {len(gone)} removed: {", ".join(gone)}' if gone else ''))


def scaffold(family, name, recs):
    code = next_code(recs, family)
    today = datetime.date.today().isoformat()
    doc = f'''code: {code}
kind: sheet
name: {name}
cls: {dict(BR='Bread', PA='Pastry', CA='Cake', CK='Cookie', CF='Confection', CR='Cream & custard', FR='Frosting', GA='Ganache').get(family, family)} ·
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
    ap.add_argument('cmd', choices=['build', 'check', 'lint', 'next-code', 'new', 'published'])
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
    elif a.cmd == 'published':
        record_published()
    elif a.cmd == 'next-code':
        print(next_code(load_recipes(), a.args[0].upper()))
    elif a.cmd == 'new':
        scaffold(a.args[0].upper(), ' '.join(a.args[1:]) or 'Untitled', load_recipes())


if __name__ == '__main__':
    main()
