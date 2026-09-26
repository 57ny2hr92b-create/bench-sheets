"""Import existing Bench Sheet .dc.html artboards into recipes/*.yaml.

One-off migration tool: parses the hand-built sheets on the Test Kitchen canvas
into the structured schema the renderer uses. Figures and schedule SVGs are
lifted verbatim into recipes/figures/. Run once, then hand-tidy the YAML.

Usage: python tools/import_dc.py <group spec> ...
  a group spec is CODE=page1.dc.html,page2.dc.html[,tent=TentCard.dc.html]
"""
import re, sys, html, pathlib, yaml
from bs4 import BeautifulSoup, NavigableString, Tag

ROOT = pathlib.Path(__file__).resolve().parents[1]
RECIPES = ROOT / 'recipes'
FIGS = RECIPES / 'figures'

GREY = '#5C5C5C'

def txt(el):
    if el is None: return ''
    return re.sub(r'\s+', ' ', el.get_text()).strip()

def name_note(td):
    """Split 'Name <span grey>· note</span>' into (name, note, dagger)."""
    name_parts, note = [], None
    for c in td.children:
        if isinstance(c, NavigableString):
            name_parts.append(str(c))
        elif c.name == 'span' and GREY in (c.get('style') or ''):
            note = txt(c).lstrip('· ').strip()
        else:
            name_parts.append(txt(c))
    name = re.sub(r'\s+', ' ', ''.join(name_parts)).strip()
    dagger = False
    if name.endswith('†'):
        name = name[:-1].strip(); dagger = True
    if note and note.endswith('†'):
        note = note[:-1].strip(); dagger = True
    return name, note, dagger

def num(s):
    s = s.replace(',', '').replace('≈', '').strip()
    if s in ('—', '', '→'): return s or '—'
    try:
        f = float(s); return int(f) if f == int(f) else f
    except ValueError:
        return s

def parse_head(soup):
    head = soup.find('div', style=re.compile('justify-content: space-between; align-items: baseline'))
    left, right = head.find_all('div', recursive=False)
    ls = [txt(s) for s in left.find_all('span')]
    rs = [txt(s) for s in right.find_all('span')]
    return dict(code=ls[0], name=ls[1], cls=ls[2] if len(ls) > 2 else '', rev=rs[0], date=rs[1], page=rs[2])

def parse_formula_table(table):
    out = {}
    thead_rows = table.find('thead').find_all('tr')
    heads = [txt(th) for th in thead_rows[-1].find_all('th')]
    stages = None
    if len(thead_rows) == 2:  # spanner
        stages = heads[3:-1]
    out['stages'] = stages
    parts = []; cur = None
    for tr in table.find('tbody').find_all('tr'):
        tds = tr.find_all('td')
        if len(tds) == 1 and tds[0].get('colspan'):
            t = tds[0]
            label = ''.join(str(c) for c in t.children if isinstance(c, NavigableString)).strip()
            note_el = t.find('span')
            m = re.match(r'([A-Z])\s+(.*)', label)
            cur = dict(id=m.group(1), name=m.group(2).strip(), rows=[])
            if note_el:
                n = txt(note_el).lstrip('· ').strip()
                if n == 'outside the formula': cur['outside'] = True
                else: cur['note'] = n
            parts.append(cur); continue
        has_box = tds[0].find('span') is not None
        if not has_box:
            # subtotal / total row
            label_td = tds[1]
            name, note, _ = name_note(label_td)
            grams = [txt(td) for td in tds[3:-1]] if stages else [txt(tds[3])]
            row = dict(label=name)
            if note: row['note'] = note
            is_last = tr is table.find('tbody').find_all('tr')[-1]
            if cur is None or cur['id'] == '' or (is_last and name.lower().startswith('total')):
                out['total'] = row
            else:
                cur['subtotal'] = row
            continue
        name, note, dagger = name_note(tds[1])
        row = dict(name=name)
        if note: row['note'] = note
        if dagger: row['dagger'] = True
        pct = txt(tds[2])
        if pct == '100.0': row['basis'] = True
        if stages:
            g = [num(txt(td)) for td in tds[3:3+len(stages)]]
            total = txt(tds[3+len(stages)])
            row['g'] = g
            if '→' in g: row['carry'] = True
            if total == '—' and not all(x in ('—','→') for x in g): row['total'] = '—'
        else:
            gtxt = txt(tds[3])
            row['g'] = num(gtxt)
            if gtxt.startswith('≈'): row['approx'] = True
        if pct == '—' and row['g'] not in ('—',) and not (cur and cur.get('outside')) and not row.get('carry'):
            row['pct'] = '—'
        if cur is None:
            cur = dict(id='', name='', rows=[]); parts.append(cur)
        cur['rows'].append(row)
    out['parts'] = parts
    return out

def parse_rail(rail):
    d = {}
    sub = rail.find('span', recursive=False)
    if sub: d['sub'] = txt(sub)
    notes = [txt(p) for p in rail.find_all('p', recursive=False)]
    if notes: d['notes'] = notes
    sbp = rail.find('div', string=None)
    for div in rail.find_all('div', recursive=False):
        if 'Scale by pan' in txt(div):
            rows = []
            for r in div.find_all('div', recursive=False)[1:]:
                a, b = [txt(s) for s in r.find_all('span')]
                bold = 'font-weight: 600' in (r.find('span').get('style') or '')
                fac, cnt = [x.strip() for x in b.split('·')]
                rows.append(dict(pan=a, factor=fac.replace('× ', '').replace('×', '').strip(), count=cnt, bold=bold) if bold else dict(pan=a, factor=fac.replace('× ', '').replace('×', '').strip(), count=cnt))
            d['scale_by_pan'] = rows
        elif 'Hands-on' in txt(div):
            d['legend'] = 'schedule'
        elif 'Start' in txt(div):
            pass
    return d

def parse_steps(ol):
    steps = []
    for li in ol.find_all('li', recursive=False):
        spans = li.find_all('span', recursive=False)
        p = li.find('p')
        strong = p.find('strong')
        head = txt(strong) if strong else ''
        if strong: strong.extract()
        text = txt(p)
        param = spans[1]
        lines = []
        cur = []
        for c in param.children:
            if isinstance(c, Tag) and c.name == 'br':
                lines.append(cur); cur = []
            else:
                cur.append(c)
        lines.append(cur)
        def render_line(parts):
            s = ''
            f = None
            for c in parts:
                if isinstance(c, NavigableString): s += str(c)
                elif c.name == 'span' and GREY in (c.get('style') or ''):
                    t = txt(c)
                    if t == '—': s += '—'
                    else: f = t
                else: s += txt(c)
            return re.sub(r'\s+', ' ', s).strip(), f
        st = dict(head=head, text=text)
        rl = [render_line(l) for l in lines]
        if rl: st['time'] = rl[0][0]
        if len(rl) > 1:
            st['target'] = rl[1][0]
            if rl[1][1]: st['target_f'] = rl[1][1]
        if len(rl) > 2:
            st['target_f'] = rl[2][0] or rl[2][1]
        steps.append(st)
    return steps

def parse_kv(container):
    rows = []
    for r in container.find_all('div', recursive=False):
        sp = r.find_all('span', recursive=False)
        if len(sp) == 2: rows.append([txt(sp[0]), txt(sp[1])])
    return rows

def parse_table_rows(table):
    heads = [txt(th) for th in table.find('thead').find_all('th')]
    rows = [[txt(td) for td in tr.find_all('td')] for tr in table.find('tbody').find_all('tr')]
    return heads, rows

def parse_sheet_page(path, code, figcount):
    soup = BeautifulSoup(path.read_text(), 'lxml')
    root = soup.find('x-dc').find('div', recursive=False)
    head = parse_head(soup)
    page = dict(head=head, sections=[])
    title = root.find('h1')
    if title:
        tb = title.parent
        page['name'] = txt(title)
        page['lede'] = txt(tb.find('p'))
        metas = tb.find_all('div', recursive=False)
        m1 = metas[0]
        for sp in m1.find_all('span', recursive=False):
            label = txt(sp.find('span'))
            val = txt(sp)[len(label):].strip()
            if label == 'Contains': val = [v.strip() for v in val.split('·')]
            page[label.lower().replace(' ', '_')] = val
        if len(metas) > 1:
            page['equipment'] = [e.strip() for e in txt(metas[1])[len('Equipment'):].split('·')]
        kf = root.find('div', style=re.compile(r'repeat\(5'))
        page['key_figures'] = [dict(label=txt(d.find_all('span')[0]), value=txt(d.find_all('span')[1])) for d in kf.find_all('div', recursive=False)]
    for sec in root.find_all('section', recursive=False):
        rail, body = sec.find_all(['div', 'table', 'ol', 'figure', 'svg'], recursive=False)[:2]
        h2 = txt(rail.find('h2'))
        s = dict(type=h2.lower().replace(' ', '_'), title=h2)
        s.update(parse_rail(rail))
        if h2 == 'Formula':
            s.update(parse_formula_table(body))
        elif h2 == 'Method' or h2 == 'Assembly':
            s['steps'] = parse_steps(body)
        elif h2 == 'Schedule' or h2 == 'Plan':
            s['type'] = 'schedule'
            fn = f'{code}-schedule.svg'; (FIGS / fn).write_text(str(body)); s['svg'] = fn
        elif body.name == 'figure' or body.find('figure') or body.name == 'svg':
            s['type'] = 'figures'
            figs = []
            container = body if body.name == 'div' else sec
            for fig in container.find_all('figure'):
                figcount[0] += 1
                fn = f'{code}-fig{figcount[0]}.svg'
                (FIGS / fn).write_text(str(fig.find('svg')))
                cap = fig.find('figcaption'); caps = cap.find_all('span')
                figs.append(dict(svg=fn, label=txt(caps[0]), caption=txt(caps[1]) if len(caps) > 1 else ''))
            s['figures'] = figs
        elif h2 == 'Done when':
            cols = body.find_all('div', recursive=False)
            s['done_when'] = parse_kv(cols[0]); s['keeps'] = parse_kv(cols[1])
        elif h2 == 'If it goes wrong':
            s['type'] = 'fixes'; s['rows'] = parse_kv(body)
        elif h2 == 'Trials':
            heads, rows = parse_table_rows(body)
            s['columns'] = heads[1:]; s['rows'] = [dict(var=r[0], values=r[1:]) for r in rows]
        elif h2 == 'Revisions':
            heads, rows = parse_table_rows(body)
            s['rows'] = [dict(rev=r[0], date=r[1], change=r[2], source=r[3]) for r in rows if any(r)]
        elif h2 == 'Batch log':
            s['type'] = 'batch_log'; s['fields'] = [txt(d.find('span')) for d in body.find_all('div', recursive=False)]
        page['sections'].append(s)
    foot = root.find_all('div', recursive=False)[-1]
    if 'Continues' in txt(foot):
        page['foot'] = txt(foot.find_all('span')[-1]).rstrip(' →')
    return page

def parse_card(path):
    soup = BeautifulSoup(path.read_text(), 'lxml')
    head = parse_head(soup)
    root = soup.find('x-dc').find('div', recursive=False)
    d = dict(code=head['code'], kind='card', name=txt(root.find('h1')), rev=head['rev'], date=head['date'])
    meta = root.find('h1').parent.find('p')
    m = {}
    cur = None
    for c in meta.children:
        if isinstance(c, Tag) and GREY in (c.get('style') or '') and txt(c) != '·':
            cur = txt(c); m[cur] = ''
        elif cur is not None:
            t = c if isinstance(c, NavigableString) else txt(c)
            if str(t).strip() != '·': m[cur] += str(t)
    d['yield'] = m.get('Yield', '').strip(); d['keeps'] = m.get('Keeps', '').strip()
    d['basis'] = m.get('Basis', '').strip().replace('% · ', '')
    d['contains'] = [x.strip() for x in m.get('Contains', '').split('·')]
    d['source'] = m.get('Source', '').strip()
    grid = root.find_all('div', recursive=False)[-1]
    left, right = grid.find_all('div', recursive=False)
    f = parse_formula_table(left.find('table'))
    d['formula'] = dict(rows=f['parts'][0]['rows'], total=f.get('total', {}).get('label', 'Total'))
    ps = left.find_all('p', recursive=False)
    if ps: d['formula_note'] = txt(ps[0])
    d['method'] = parse_steps(right.find('ol'))
    note = right.find_all('p', recursive=False)
    if note: d['note'] = txt(note[-1])
    return d

def parse_tent(path):
    soup = BeautifulSoup(path.read_text(), 'lxml')
    face = soup.find('x-dc').find('div', recursive=False).find_all('div', recursive=False)[-1]
    return dict(name=txt(face.find('h2')), note=txt(face.find('p')))

def main(specs):
    FIGS.mkdir(parents=True, exist_ok=True)
    for spec in specs:
        code, files = spec.split('=', 1)
        pages = []; tent = None
        for f in files.split(','):
            if f.startswith('tent='):
                tent = parse_tent(ROOT / 'tools/originals' / f[5:]); continue
            pages.append(ROOT / 'tools/originals' / f)
        if len(pages) == 1 and 'Card' in pages[0].read_text()[:3000] and '/ ' not in pages[0].read_text()[:1500]:
            d = parse_card(pages[0])
        else:
            figcount = [0]
            parsed = [parse_sheet_page(p, code, figcount) for p in pages]
            p1 = parsed[0]
            d = dict(code=code, kind='sheet', name=p1['name'], cls=p1['head']['cls'], lede=p1['lede'],
                     source=p1['source'], contains=p1['contains'], equipment=p1.get('equipment', []),
                     key_figures=p1['key_figures'], last_change=p1.get('last_change'))
            sections = []
            for pg in parsed:
                for s in pg['sections']: sections.append(s)
            # gather
            meth = [s for s in sections if s['type'] in ('method', 'assembly')]
            d['method_rail'] = [dict(sub=s.get('sub'), notes=s.get('notes')) for s in meth]
            d['method'] = [st for s in meth for st in s['steps']]
            for s in sections:
                if s['type'] == 'formula':
                    d['formula'] = dict(basis=s.get('sub', ''), notes=s.get('notes', []), parts=s['parts'])
                    if s.get('stages'): d['formula']['stages'] = s['stages']
                    if s.get('total'): d['formula']['total'] = s['total']
                    if s.get('scale_by_pan'): d['formula']['scale_by_pan'] = s['scale_by_pan']
                elif s['type'] == 'schedule':
                    d['schedule'] = dict(sub=s.get('sub'), notes=s.get('notes'), svg=s['svg'])
                elif s['type'] == 'figures':
                    d['figures'] = dict(title=s['title'], sub=s.get('sub'), items=s['figures'])
                elif s['type'] == 'done_when':
                    d['done_when'] = s['done_when']; d['keeps'] = s['keeps']
                elif s['type'] == 'fixes':
                    d['fixes'] = dict(sub=s.get('sub'), rows=s['rows'])
                elif s['type'] == 'trials':
                    d['trials'] = dict(sub=s.get('sub'), notes=s.get('notes'), columns=s['columns'], rows=s['rows'])
                elif s['type'] == 'revisions':
                    d['revisions'] = s['rows']
                elif s['type'] == 'batch_log':
                    d['batch_log'] = s['fields']
            # page plan
            plan = []
            n = 0
            for pg in parsed:
                names = []
                for s in pg['sections']:
                    if s['type'] in ('method', 'assembly'):
                        k = len(s['steps']); names.append(f'method:{n+1}-{n+k}'); n += k
                    else: names.append(s['type'])
                plan.append(names)
            d['pages'] = plan
            d['foot'] = p1.get('foot')
            if tent: d['tent'] = tent
        out = RECIPES / f'{code}.yaml'
        out.write_text(yaml.safe_dump(d, sort_keys=False, allow_unicode=True, width=100))
        print('wrote', out)

if __name__ == '__main__':
    main(sys.argv[1:])
