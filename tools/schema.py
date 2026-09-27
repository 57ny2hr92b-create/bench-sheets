"""Lint for recipe YAML: the things that would otherwise surface as a wrong sheet on the bench.

Errors stop the build. Warnings print but pass. Run: python build.py lint
"""
import re, datetime, pathlib

CODE = re.compile(r'^[A-Z]{2}-\d{3}$')
DATE = re.compile(r'^\d{4}-\d{2}-\d{2}$')
ALLERGENS = {'Wheat', 'Milk', 'Egg', 'Nuts', 'Tree nuts', 'Peanut', 'Soy', 'Sesame', 'Fish', 'Shellfish', 'None'}
KINDS = {'sheet', 'card'}
ROW_KEYS = {'name', 'note', 'g', 'basis', 'dagger', 'approx', 'pct', 'carry', 'total', 'outside'}
STATUSES = ('draft', 'trial', 'standard', 'retired')
SECTIONS = {'formula', 'components', 'schedule', 'method', 'figures', 'done_when', 'fixes', 'trials', 'revisions', 'batch_log'}
SHEET_REQUIRED = ['code', 'name', 'cls', 'lede', 'source', 'contains', 'key_figures', 'formula', 'method', 'done_when', 'keeps', 'revisions']
CARD_REQUIRED = ['code', 'name', 'yield', 'keeps', 'basis', 'contains', 'source', 'formula', 'method', 'revisions']


class Lint:
    def __init__(self):
        self.errors, self.warnings = [], []

    def err(self, code, msg): self.errors.append(f'{code}: {msg}')
    def warn(self, code, msg): self.warnings.append(f'{code}: {msg}')


def _rows(F):
    for part in F.get('parts', [{'rows': F.get('rows', [])}]):
        for row in part.get('rows', []):
            yield part, row


def lint_recipe(r, lib, recs, L, figs_dir):
    code = r.get('code', r.get('_file', '?'))
    kind = r.get('kind', 'sheet')
    if kind not in KINDS: L.err(code, f'kind must be one of {sorted(KINDS)}')
    if r.get('status', 'standard') not in STATUSES: L.err(code, f'status must be one of {STATUSES}')
    if not CODE.match(str(r.get('code', ''))): L.err(code, 'code must look like BR-023')
    if r.get('_file') and r['_file'] != f'{r.get("code")}.yaml': L.err(code, f'file is named {r["_file"]}; rename it to {r.get("code")}.yaml')
    fam = str(r.get('code', ''))[:2]
    if fam not in {f['code'] for f in lib['families']}: L.err(code, f'family {fam} is not in library.yaml')
    for k in (SHEET_REQUIRED if kind == 'sheet' else CARD_REQUIRED):
        if k not in r or r[k] in (None, '', []): L.err(code, f'missing {k}')
    # allergens
    for a in r.get('contains') or []:
        base = a.split(' ')[0]
        if base not in ALLERGENS and a not in ALLERGENS: L.warn(code, f'contains "{a}" is not a standard allergen name ({", ".join(sorted(ALLERGENS))})')
    # key figures
    if kind == 'sheet':
        kf = r.get('key_figures') or []
        if len(kf) != 5: L.err(code, f'key_figures needs exactly 5 entries (has {len(kf)})')
        for f in kf:
            if not f.get('label') or f.get('value') in (None, ''): L.err(code, f'key figure {f} needs a label and a value')
    # formula
    F = r.get('formula') or {}
    parts = F.get('parts') if kind == 'sheet' else [dict(rows=F.get('rows', []))]
    if not parts: L.err(code, 'formula has no parts/rows')
    seen_ids = set()
    for part in parts or []:
        pid = part.get('id')
        if kind == 'sheet' and pid:
            if pid in seen_ids: L.err(code, f'part id {pid} repeated')
            seen_ids.add(pid)
        for row in part.get('rows', []):
            if not row.get('name'): L.err(code, f'formula row without a name in part {pid}')
            stray = set(row) - ROW_KEYS
            if stray: L.err(code, f'{row.get("name")}: unknown row keys {sorted(stray)} — a note with a comma must be quoted')
            g = row.get('g')
            if g is None and not row.get('carry'): L.err(code, f'{row.get("name")}: no grams (use "—" for none)')
            if isinstance(g, list) and F.get('stages') and len(g) != len(F['stages']):
                L.err(code, f'{row["name"]}: {len(g)} stage values for {len(F["stages"])} stages')
            if isinstance(g, str) and g not in ('—', '') and not re.match(r'^[\d.,–-]+$', g) and not row.get('approx'):
                L.warn(code, f'{row["name"]}: grams "{g}" is text; the sheet will print it as-is')
    basis_rows = [row for _, row in _rows(F) if row.get('basis')]
    if kind == 'sheet' and not basis_rows and 'flour' in str(F.get('basis', '')).lower():
        L.err(code, 'basis says flour = 100 but no row is flagged basis: true')
    # method
    steps = r.get('method') or []
    for i, s in enumerate(steps, 1):
        if not s.get('head') or not str(s['head']).endswith('.'): L.err(code, f'step {i}: head must be a word ending in a period ("Mix.")')
        if 'text' not in s: L.err(code, f'step {i}: no text')
        if kind == 'sheet' and 'time' not in s: L.warn(code, f'step {i}: no time (use "—")')
        if kind == 'card' and len(str(s.get('text', ''))) > 78: L.warn(code, f'step {i}: card steps over ~70 characters run to three lines')
    # pages cover every step exactly once
    if kind == 'sheet' and r.get('pages'):
        covered = []
        for p in r['pages']:
            for sec in p:
                name, _, rng = sec.partition(':')
                if name not in SECTIONS: L.err(code, f'pages: unknown section "{name}"')
                if name == 'method':
                    if rng:
                        a, _, b = rng.partition('-'); covered += list(range(int(a), int(b or a) + 1))
                    else:
                        covered += list(range(1, len(steps) + 1))
                if name in ('figures', 'schedule', 'fixes', 'trials', 'components', 'batch_log') and not r.get(name):
                    L.err(code, f'pages lists {name} but the recipe has no {name}')
        if sorted(covered) != list(range(1, len(steps) + 1)):
            L.err(code, f'pages cover method steps {sorted(covered)} but there are {len(steps)} steps')
    # figures / schedule svgs exist
    for it in (r.get('figures') or {}).get('items', []):
        if not (figs_dir / it.get('svg', '')).exists(): L.err(code, f'figure file {it.get("svg")} not found in recipes/figures/')
    if (r.get('schedule') or {}).get('svg') and not (figs_dir / r['schedule']['svg']).exists():
        L.err(code, f'schedule svg {r["schedule"]["svg"]} not found')
    # two-column lists
    for key in (('done_when', 'keeps') if kind == 'sheet' else ()):
        for row in r.get(key) or []:
            if not (isinstance(row, list) and len(row) == 2):
                L.err(code, f'{key} row {row!r} must be [label, text] — quote text that contains commas')
    for row in (r.get('fixes') or {}).get('rows', []):
        if not (isinstance(row, list) and len(row) == 2):
            L.err(code, f'fixes row {row!r} must be [symptom, cause and fix] — quote text that contains commas')
    # revisions
    revs = r.get('revisions') or []
    last_n = 0
    for rv in revs:
        m = re.match(r'^(?:Rev )?(\d+)$', str(rv.get('rev', '')))
        if not m: L.err(code, f'revision "{rv.get("rev")}" must be "Rev 01" style'); continue
        n = int(m.group(1))
        if n != last_n + 1: L.err(code, f'revisions must run 01, 02, … without gaps (found Rev {n:02d} after Rev {last_n:02d})')
        last_n = n
        d = rv.get('date')
        if d not in (None, '—') and not DATE.match(str(d)): L.err(code, f'Rev {n:02d} date "{d}" is not YYYY-MM-DD')
        if not rv.get('change'): L.err(code, f'Rev {n:02d} has no change note')
    if revs and revs[-1].get('date') in (None, '—'): L.warn(code, 'newest revision has no date; the running head will show —')
    # cross-links
    for u in r.get('uses', []):
        if u not in recs: L.err(code, f'uses {u}, which does not exist')
    # tent
    if r.get('tent') and not r['tent'].get('name'): L.err(code, 'tent needs a name')


def lint_library(lib, recs, L):
    codes = [f['code'] for f in lib['families']]
    if len(codes) != len(set(codes)): L.err('library', 'duplicate family codes')
    if not DATE.match(str(lib['index'].get('date', ''))): L.err('library', 'index.date must be YYYY-MM-DD')
    if not isinstance(lib['index'].get('rev'), int): L.err('library', 'index.rev must be an integer')


def run(lib, recs, figs_dir):
    L = Lint()
    lint_library(lib, recs, L)
    for r in recs.values():
        lint_recipe(r, lib, recs, L, pathlib.Path(figs_dir))
    for w in L.warnings: print('  warn', w)
    for e in L.errors: print('  ERROR', e)
    return L
