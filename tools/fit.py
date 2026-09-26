"""Fit check: render each artboard in Chromium with the real IBM Plex Sans and report overflows.

Rules (from the Bench Sheet README): every section bottom <= 968 px on Letter (448 on a card),
no method step wider than two lines, no ingredient name wrapping, meta row 1 on one line.
Tent cards are full-bleed (528 x 816) and have no content limit beyond the board itself.

Fonts: `npm pack @fontsource/ibm-plex-sans` once into tools/fonts/ (Google Fonts is not
reachable from most shells). Run: python build.py check
"""
import re, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
FONT_DIR = ROOT / 'tools' / 'fonts' / 'package' / 'files'
LIMITS = {1056: 968, 480: 448}


def font_css():
    if not FONT_DIR.exists():
        print('  (no local Plex fonts: run  cd tools/fonts && npm pack @fontsource/ibm-plex-sans && tar xzf *.tgz)')
        return ''
    return ''.join(f"@font-face{{font-family:'IBM Plex Sans';font-weight:{w};src:url('file://{FONT_DIR}/ibm-plex-sans-latin-{w}-normal.woff2') format('woff2')}}" for w in (400, 500, 600))


MEASURE = """() => {
  const root = document.body.firstElementChild;
  const kids = [...root.children];
  // the page foot (margin-top:auto, 'Continues on…' / index foot) is pinned to the bottom and is not content
  const isFoot = e => /margin-top:\\s*auto/.test(e.getAttribute('style') || '');
  const content = kids.filter(e => !isFoot(e));
  const bottom = Math.max(...content.map(e => Math.round(e.getBoundingClientRect().bottom)));
  // lines of a step = height of the text itself (a Range), not of the <p>, which a two-line
  // parameter column can stretch
  const lines = p => { const r = document.createRange(); r.selectNodeContents(p); const h = r.getBoundingClientRect().height; return Math.round(h / parseFloat(getComputedStyle(p).lineHeight)); };
  const tall = [...document.querySelectorAll('li p')].filter(p => lines(p) > 2).map(p => p.textContent.slice(0, 60));
  // an ingredient cell that wraps is taller than one line of its own font (formula tables only;
  // the index name column is allowed to run to two lines)
  const formulaTables = [...document.querySelectorAll('table')].filter(t => /Ingredient/.test(t.querySelector('thead')?.textContent || ''));
  const wraps = formulaTables.flatMap(t => [...t.querySelectorAll('tbody td')]).filter(td => {
    if (td.getAttribute('colspan') || !td.textContent.trim()) return false;
    const lh = parseFloat(getComputedStyle(td).lineHeight); if (!lh) return false;
    const r = document.createRange(); r.selectNodeContents(td);
    return r.getBoundingClientRect().height > lh * 1.5;
  }).map(td => td.textContent.trim().slice(0, 50));
  const meta = [...root.querySelectorAll('div')].filter(d => d.textContent.trim().startsWith('Source')).map(d => d.scrollWidth - d.clientWidth);
  return {bottom, tall, wraps, meta};}"""


def check(files, screenshots=None):
    from playwright.sync_api import sync_playwright
    faces = font_css()
    problems = 0
    tmp = ROOT / 'out' / '_render.html'
    with sync_playwright() as pw:
        b = pw.chromium.launch(); pg = b.new_page()
        for f in files:
            src = pathlib.Path(f).read_text()
            inner = re.search(r'</helmet>\s*(.*?)\s*</x-dc>', src, re.S).group(1)
            w, h = map(int, re.search(r'"\$preview":\{"width":(\d+),"height":(\d+)', src).groups())
            pg.set_viewport_size({'width': w, 'height': h})
            tmp.write_text(f"<!doctype html><html><head><style>{faces}body{{margin:0}}</style></head><body>{inner}</body></html>")
            pg.goto('file://' + str(tmp)); pg.wait_for_timeout(250)
            r = pg.evaluate(MEASURE)
            limit = LIMITS.get(h, h)
            issues = []
            if r['bottom'] > limit: issues.append(f"content ends at {r['bottom']} px (limit {limit})")
            for t in r['tall']: issues.append(f'3-line step: {t}')
            for t in r['wraps']: issues.append(f'wrapped cell: {t}')
            for m in r['meta']:
                if m > 0: issues.append(f'meta row 1 overflows by {m} px')
            name = pathlib.Path(f).name
            print(f"{'ok' if not issues else 'FIX':>3}  {name:28s} bottom {r['bottom']:4d}/{limit}")
            for i in issues: print('       -', i)
            problems += len(issues)
            if screenshots:
                pg.screenshot(path=str(pathlib.Path(screenshots) / name.replace('.dc.html', '.png')))
        b.close()
    tmp.unlink(missing_ok=True)
    print('all artboards fit' if not problems else f'{problems} problem(s)')
    return problems


if __name__ == '__main__':
    sys.exit(1 if check(sys.argv[1:]) else 0)
