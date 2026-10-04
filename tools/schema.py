"""Lint for recipe YAML: the things that would otherwise surface as a wrong sheet on the bench.

Errors stop the build. Warnings print but pass. Run: python build.py lint
"""
import re, datetime, pathlib, math

SCHEMA_VERSION = 1

CODE = re.compile(r'^[A-Z]{2}-\d{3}$')
DATE = re.compile(r'^\d{4}-\d{2}-\d{2}$')
ALLERGENS = {'Wheat', 'Milk', 'Egg', 'Nuts', 'Tree nuts', 'Peanut', 'Soy', 'Sesame', 'Fish', 'Shellfish', 'None'}
KINDS = {'sheet', 'card'}
ROW_KEYS = {'name', 'note', 'g', 'basis', 'dagger', 'approx', 'pct', 'carry', 'total', 'outside'}
STATUSES = ('draft', 'trial', 'standard', 'retired')
SECTIONS = {'formula', 'components', 'schedule', 'method', 'figures', 'done_when', 'fixes', 'trials', 'revisions', 'batch_log', 'variants'}
# Reading order across the sheet (the design system's page anatomy): make it, then judge it, then record it.
# method chunks run in step order; figures and variants may sit between chunks (the steps point to them);
# nothing that judges the bake (done when, fixes) may come before the last method step. Two sections
# float: trials (its variable is chosen before mixing) and the batch log (a blank form); either may sit
# beside the steps to balance a long sheet. Trials always precedes revisions.
ORDER = {'formula': 0, 'components': 1, 'schedule': 2, 'method': 3, 'figures': 3, 'variants': 3,
         'done_when': 4, 'fixes': 5, 'trials': None, 'revisions': 7, 'batch_log': None}
VARIANT_KEYS = {'name', 'note', 'rows', 'steps'}
SHEET_REQUIRED = ['code', 'name', 'cls', 'lede', 'source', 'contains', 'key_figures', 'formula', 'method', 'done_when', 'keeps', 'revisions']
CARD_REQUIRED = ['code', 'name', 'yield', 'keeps', 'basis', 'contains', 'source', 'formula', 'method', 'revisions']
ROOT_KEYS = set(SHEET_REQUIRED + CARD_REQUIRED) | {
    '_file', 'schema_version', 'kind', 'status', 'equipment', 'uses', 'method_rail',
    'pages', 'schedule', 'figures', 'components', 'fixes', 'trials', 'batch_log',
    'variants', 'tent', 'dense', 'revisions_blank', 'foot', 'last_change', 'formula_note', 'note',
}


class Lint:
    def __init__(self):
        self.errors, self.warnings = [], []
        self.diagnostics = []

    def _add(self, severity, code, msg, path, file, rule):
        target = self.errors if severity == 'error' else self.warnings
        target.append(f'{code}: {msg}')
        if file is None:
            file = 'library.yaml' if code == 'library' else f'recipes/{code}.yaml'
        self.diagnostics.append(dict(code=code, file=file, path=path, severity=severity, message=msg, rule=rule))

    def err(self, code, msg, path='$', file=None, rule='recipe.invalid'):
        self._add('error', code, msg, path, file, rule)

    def warn(self, code, msg, path='$', file=None, rule='recipe.warning'):
        self._add('warning', code, msg, path, file, rule)


class _Shape:
    """Small input guards for semantic lint, not a second schema or a coercing parser."""
    def __init__(self, code, lint):
        self.code, self.lint = code, lint
        self.valid = True

    def expect(self, value, types, path):
        types = types if isinstance(types, tuple) else (types,)
        if type(value) in types:
            return True
        names = {dict: 'mapping', list: 'list', str: 'string', bool: 'boolean', int: 'integer', float: 'number'}
        wanted = ' or '.join(names.get(t, t.__name__) for t in types)
        self.lint.err(self.code, f'{path}: expected {wanted}; got {type(value).__name__}', path=path, rule='input.type')
        self.valid = False
        return False

    def mapping(self, value, path):
        return value if self.expect(value, dict, path) else {}

    def items(self, value, path, item_type):
        if self.expect(value, list, path):
            for i, item in enumerate(value):
                location = f'{path}[{i}]'
                if self.expect(item, item_type, location):
                    yield item, location

    def fields(self, obj, path='', strings=(), booleans=()):
        for fields, kind in ((strings, str), (booleans, bool)):
            for key in fields:
                if key in obj:
                    self.expect(obj[key], kind, f'{path}.{key}' if path else key)

    def strings(self, obj, key, path=''):
        if key in obj:
            # Historical rail/schedule notes use explicit null for no notes.
            if key == 'notes' and obj[key] is None:
                return
            list(self.items(obj[key], f'{path}.{key}' if path else key, str))


def _recipe_shapes(r, code, L):
    """Guard common authoring structures before any semantic rule traverses them."""
    s = _Shape(code, L)
    s.fields(r, strings=('code', 'kind', 'status', 'name', 'cls', 'lede', 'source', 'yield', 'basis'),
             booleans=('dense', 'revisions_blank'))
    for key in ('contains', 'equipment', 'uses', 'batch_log'):
        s.strings(r, key)
    for key in sorted(set(r) - ROOT_KEYS, key=str):
        L.warn(code, f'{key}: unrecognized root field; retained in source but may not be rendered', path=str(key), rule='field.unknown')

    def rows(obj, path, stages=None):
        if 'rows' not in obj:
            L.err(code, f'{path}: no rows; expected a list of ingredient mappings', path=path + '.rows', rule='input.type')
            s.valid = False
            return
        for row, p in s.items(obj.get('rows'), f'{path}.rows', dict):
            s.fields(row, p, strings=('name', 'note'), booleans=('basis', 'carry', 'outside', 'dagger', 'approx'))
            lint_grams(row, code, L, p + '.g', stages)
            for key in sorted(set(row) - ROW_KEYS, key=str):
                L.err(code, f'{p}.{key}: unknown row key — quote notes containing commas', path=f'{p}.{key}', rule='field.unknown')

    if 'formula' in r:
        f = s.mapping(r['formula'], 'formula')
        s.strings(f, 'stages', 'formula')
        s.strings(f, 'notes', 'formula')
        if r.get('kind', 'sheet') == 'card':
            rows(f, 'formula')
        if f.get('total') is not None:
            s.expect(f['total'], str if r.get('kind') == 'card' else dict, 'formula.total')
        if 'parts' in f:
            for part, p in s.items(f['parts'], 'formula.parts', dict):
                s.fields(part, p, strings=('id', 'name', 'note'), booleans=('outside',))
                if part.get('subtotal') is not None:
                    s.expect(part['subtotal'], dict, p + '.subtotal')
                rows(part, p, f.get('stages') if isinstance(f.get('stages'), list) else None)
    for key in ('method', 'revisions', 'key_figures', 'method_rail'):
        if key not in r:
            continue
        for item, p in s.items(r[key], key, dict):
            if key == 'method':
                s.fields(item, p, strings=('head', 'text', 'time', 'target', 'target_f'))
            elif key == 'key_figures':
                s.fields(item, p, strings=('label',))
                if 'value' in item:
                    s.expect(item['value'], (str, int, float), p + '.value')
            elif key == 'method_rail':
                s.strings(item, 'notes', p)
    for key in ('schedule', 'figures', 'fixes', 'trials', 'components', 'tent', 'variants'):
        if key not in r:
            continue
        obj = s.mapping(r[key], key)
        s.strings(obj, 'notes', key)
        if key == 'schedule':
            s.fields(obj, key, strings=('svg',))
        if key == 'figures':
            for it, p in s.items(obj.get('items'), key + '.items', dict):
                s.fields(it, p, strings=('svg', 'gen', 'label', 'caption'), booleans=('below',))
        if key == 'variants' and 'items' in obj:
            for it, p in s.items(obj['items'], key + '.items', dict):
                s.fields(it, p, strings=('name', 'note'))
                s.strings(it, 'steps', p)
                for extra in sorted(set(it) - VARIANT_KEYS, key=str):
                    L.err(code, f'{p}: unknown keys {extra!r} (allowed: {sorted(VARIANT_KEYS)})', path=f'{p}.{extra}', rule='field.unknown')
                rows(it, p)
        if key in ('trials', 'components') and 'rows' in obj:
            list(s.items(obj['rows'], key + '.rows', dict))
        if key == 'fixes' and 'rows' in obj:
            pairs(obj['rows'], key + '.rows', s)
    if r.get('kind', 'sheet') == 'sheet':
        for key in ('done_when', 'keeps'):
            if key in r:
                pairs(r[key], key, s)
    elif 'keeps' in r:
        s.expect(r['keeps'], str, 'keeps')
    if 'pages' in r:
        for page, p in s.items(r['pages'], 'pages', list):
            for token, loc in s.items(page, p, str):
                if ':' not in token:
                    continue
                match = re.fullmatch(r'method:([1-9][0-9]*)(?:-([1-9][0-9]*))?', token)
                count = len(r['method']) if isinstance(r.get('method'), list) else 0
                # Length bound avoids huge integers before conversion; steps already bounds valid ranges.
                valid = match and all(len(n) <= len(str(count)) for n in match.groups() if n)
                if valid:
                    a, b = int(match[1]), int(match[2] or match[1])
                    valid = 1 <= a <= b <= count
                if not valid:
                    L.err(code, f'{loc}: use method:a-b within the {count} method steps; got {token!r}', path=loc, rule='pages.range')
                    s.valid = False
    return s.valid


def pairs(value, path, shape):
    for row, p in shape.items(value, path, list):
        if len(row) != 2:
            shape.lint.err(shape.code, f'{p}: expected [label, text]; quote text containing commas', path=p, rule='input.type')
            shape.valid = False
        else:
            for i, part in enumerate(row):
                shape.expect(part, str, f'{p}[{i}]')


def _rows(F):
    for part in F.get('parts', [{'rows': F.get('rows', [])}]):
        for row in part.get('rows', []):
            yield part, row


def lint_grams(row, code, L, path, stages=None):
    """Accept only quantities the arithmetic understands, plus explicit placeholders."""
    g = row.get('g')
    name = row.get('name', '?')

    def scalar(value, field):
        if type(value) in (int, float):
            if value >= 0 and (type(value) is int or math.isfinite(value)):
                return
        elif value == '—' or (value == '→' and row.get('carry') is True):
            return
        L.err(code, f'{field} ({name}): expected a finite, non-negative number in grams '
              f'or "—" ("→" only with carry: true); got {value!r}. '
              'Remove quotes around numeric weights; put quantity words or ranges in note.', path=field, rule='quantity.invalid')

    if stages:
        if not isinstance(g, list):
            L.err(code, f'{path} ({name}): expected a list of {len(stages)} stage quantities; got {g!r}', path=path, rule='quantity.stage-count')
            return
        if len(g) != len(stages):
            L.err(code, f'{path} ({name}): {len(g)} stage values for {len(stages)} stages', path=path, rule='quantity.stage-count')
        for i, value in enumerate(g):
            scalar(value, f'{path}[{i}]')
    else:
        scalar(g, path)


def lint_recipe(r, lib, recs, L, figs_dir):
    if not isinstance(r, dict):
        L.err('input', 'expected a recipe mapping', rule='input.type')
        return
    if any(d['code'] == 'library' and d['severity'] == 'error' for d in L.diagnostics):
        return
    code = r.get('code', r.get('_file', '?'))
    version = r.get('schema_version', SCHEMA_VERSION)
    if type(version) is not int or version != SCHEMA_VERSION:
        L.err(code, f'schema_version must be {SCHEMA_VERSION}; got {version!r}', path='schema_version', rule='schema.version')
        return
    if not _recipe_shapes(r, code, L):
        return
    kind = r.get('kind', 'sheet')
    if kind not in KINDS: L.err(code, f'kind must be one of {sorted(KINDS)}')
    if r.get('status', 'standard') not in STATUSES: L.err(code, f'status must be one of {STATUSES}')
    if not CODE.match(str(r.get('code', ''))): L.err(code, 'code must look like BR-023')
    if r.get('_file') and r['_file'] != f'{r.get("code")}.yaml': L.err(code, f'file is named {r["_file"]}; rename it to {r.get("code")}.yaml')
    fam = str(r.get('code', ''))[:2]
    if fam not in {f['code'] for f in lib['families']}: L.err(code, f'family {fam} is not in library.yaml')
    for k in (SHEET_REQUIRED if kind == 'sheet' else CARD_REQUIRED):
        if k not in r or r[k] in (None, '', []): L.err(code, f'missing {k}', path=k)
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
    for pi, part in enumerate(parts or []):
        pid = part.get('id')
        if kind == 'sheet' and pid:
            if pid in seen_ids: L.err(code, f'part id {pid} repeated')
            seen_ids.add(pid)
        for ri, row in enumerate(part.get('rows', [])):
            if not row.get('name'): L.err(code, f'formula row without a name in part {pid}')
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
                if name in ('figures', 'schedule', 'fixes', 'trials', 'components', 'batch_log', 'variants') and not r.get(name):
                    L.err(code, f'pages lists {name} but the recipe has no {name}')
        if sorted(covered) != list(range(1, len(steps) + 1)):
            L.err(code, f'pages cover method steps {sorted(covered)} but there are {len(steps)} steps')
        # reading order
        flat = [sec.partition(':')[0] for p in r['pages'] for sec in p]
        fixed = [n for n in flat if ORDER.get(n) is not None]
        ranks = [ORDER[n] for n in fixed]
        if ranks != sorted(ranks):
            bad = next(fixed[i] for i in range(1, len(fixed)) if ranks[i] < ranks[i - 1])
            L.err(code, f'pages: "{bad}" comes before a section that belongs earlier — order is formula, schedule, method (figures/variants beside their steps), done_when, fixes, revisions; trials and batch_log float after the formula (trials before revisions)')
        if 'trials' in flat and flat.index('trials') < flat.index('formula') + 1 if 'formula' in flat else False:
            L.err(code, 'pages: trials before the formula')
        if 'trials' in flat and 'revisions' in flat and flat.index('trials') > flat.index('revisions'):
            L.err(code, 'pages: trials must come before revisions')
        if covered != sorted(covered):
            L.err(code, 'pages: method chunks must run in step order')
        for name in ('done_when', 'revisions'):
            if name not in flat: L.err(code, f'pages never places {name}; every sheet shows it after the last step')
        for name in ('fixes', 'trials', 'batch_log'):
            if r.get(name) and name not in flat: L.warn(code, f'recipe has {name} but pages never places it')
    # variants: named sub-formulas on top of the main formula, each a % of it
    V = r.get('variants')
    if V is not None:
        items = V.get('items') if isinstance(V, dict) else None
        if not items: L.err(code, 'variants needs items: a list of named variants')
        for i, v in enumerate(items or [], 1):
            if not v.get('name'): L.err(code, f'variant {i}: no name')
            if not v.get('rows'): L.err(code, f'variant {v.get("name", i)}: no rows')
            for ri, row in enumerate(v.get('rows') or []):
                if not row.get('name'): L.err(code, f'variant {v.get("name")}: row without a name')
            for s in v.get('steps') or []:
                if not isinstance(s, str): L.err(code, f'variant {v.get("name")}: steps are one-line strings')
                elif len(s) > 60: L.warn(code, f'variant {v.get("name")}: step "{s[:30]}…" over ~60 characters will wrap in a two-column layout')
        if kind == 'sheet' and r.get('pages') and not any(sec == 'variants' for p in r['pages'] for sec in p):
            L.warn(code, 'recipe has variants but pages never places the variants section')
    # figures / schedule svgs exist
    for i, it in enumerate((r.get('figures') or {}).get('items', [])):
        path = f'figures.items[{i}]'
        if bool(it.get('gen')) == bool(it.get('svg')):
            L.err(code, f'{path}: give exactly one of gen or svg', path=path, rule='figure.invalid')
        elif it.get('gen'):
            from tools import figures as figgen
            try: figgen.render(it)
            except figgen.FigureError as e: L.err(code, f'{path}: {e}', path=path, rule='figure.invalid')
            except Exception as e: L.err(code, f'{path}: {type(e).__name__}: {e}', path=path, rule='figure.invalid')
        elif not (figs_dir / it['svg']).is_file():
            L.err(code, f'{path}: figure file {it["svg"]} not found in recipes/figures/', path=path, rule='figure.invalid')
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
    s = _Shape('library', L)
    lib = s.mapping(lib, '$')
    for f, p in s.items(lib.get('families'), 'families', dict):
        s.expect(f.get('code'), str, p + '.code')
        s.expect(f.get('name'), str, p + '.name')
    s.mapping(lib.get('index'), 'index')
    if not s.valid:
        return
    codes = [f['code'] for f in lib['families']]
    if len(codes) != len(set(codes)): L.err('library', 'duplicate family codes')
    if not DATE.match(str(lib['index'].get('date', ''))): L.err('library', 'index.date must be YYYY-MM-DD')
    if not isinstance(lib['index'].get('rev'), int): L.err('library', 'index.rev must be an integer')


def run(lib, recs, figs_dir, quiet=False):
    L = Lint()
    lint_library(lib, recs, L)
    for r in recs.values():
        lint_recipe(r, lib, recs, L, pathlib.Path(figs_dir))
    if not quiet:
        for w in L.warnings: print('  warn', w)
        for e in L.errors: print('  ERROR', e)
    return L
