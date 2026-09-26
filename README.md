# Bench sheets

The test-kitchen recipe library as data. Each recipe is one YAML file; `build.py` renders every
Bench Sheet, component card and tent card, the library index, and the canvas layout that goes to the
**Test Kitchen** artifact. Nothing on the canvas is hand-edited any more — if it's wrong, fix the
YAML and rebuild.

```
recipes/            one file per recipe, named by code (BR-023.yaml). This is the record.
recipes/figures/    SVG figures and schedules, referenced by file name
library.yaml        families, index rev/date, canvas settings
published.yaml      what is currently on the canvas (written by `build.py published`)
templates/          Jinja2 templates that own the Bench Sheet markup
tools/schema.py     lint (runs before every build)
tools/fit.py        Chromium fit check with the real IBM Plex Sans
tools/import_dc.py  one-off importer for hand-built artboards (how the first six got in)
tests/              pytest regression suite
out/                build output (ignored by git)
```

## Setup

```
pip install -r requirements.txt
python -m playwright install chromium           # for `check`
cd tools/fonts && npm pack @fontsource/ibm-plex-sans@5 && tar xzf *.tgz && cd ../..
```

## Everyday commands

| Command | What it does |
|---|---|
| `python build.py lint` | Validate every recipe. Errors name the file and the field. |
| `python build.py build` | Lint, then render `out/project/*.dc.html`, `Index.dc.html`, `canvas.json`, and `out/publish.json`. |
| `python build.py check` | Build, then render every artboard in Chromium and fail if anything overflows, a step runs to three lines, an ingredient wraps, or the meta row breaks. Screenshots land in `out/shots/`. |
| `python build.py new CA "Olive oil cake"` | Scaffold `recipes/CA-012.yaml` with the next free code. |
| `python build.py next-code BR` | Just print the next free code. |
| `python build.py published` | After a successful publish, record this build as what is on the canvas. |
| `python build.py pdf [CODE …]` | Print `out/pdf/CODE.pdf` (all pages of a sheet; tent and cards as their own files at their own size). No codes = every live recipe. |
| `python -m pytest -q` | Regression tests (math, links, rendering, fit). |

## Recipe status

Every recipe has a `status`: `draft` → `trial` → `standard` → (`retired`).

- **draft** — renders to `out/drafts/` for review and PDF, but never reaches the canvas or the index. Lint errors on a draft are reported and the draft is skipped; they never block the build. New recipes scaffold as drafts.
- **trial** — on the canvas and in the index, marked "· trial" in the Format column.
- **standard** — the default when the field is absent; the binder.
- **retired** — kept in the repo as the record (history, revisions, cross-links from old sheets still resolve in git), not rendered, not indexed. Retire rather than delete.

## Adding a recipe

1. `python build.py new <FAMILY> "<Name>"` — families are `BR PA CA CK CF CR FR GA` (see `library.yaml`; add a family there before using a new prefix).
2. Fill in the YAML. Grams only; percentages, subtotals, totals, the scale-by-weight divisor, step numbers, Rev/date in the running head, index rows and cross-links are all computed.
3. Set `status: trial` (or `standard`) when it's ready for the canvas; leave it `draft` while you work — `python build.py pdf CODE` prints a draft too.
4. `python build.py check`. Fix whatever it flags — shorten a step, move a section to the next page in `pages:`, drop the blank revisions row (`revisions_blank: false`). Don't shrink type or padding; those are the design system's.
5. Bump `index.rev` and `index.date` in `library.yaml` (any new row or Rev change is a new index rev).
6. Publish `out/publish.json` to the canvas (below), then `python build.py published`, then commit.

## Revising a recipe

Append a row to `revisions:`. Never edit or delete an older row — the running head, the "Last change"
line and the index Rev all derive from the newest row, and the older rows are the history. Bump the
index rev in `library.yaml`.

## Publishing to the canvas

`out/publish.json` is the exact `files` map for the Artifact publish: every rendered artboard plus
`canvas.json`, and a `null` for any artboard `published.yaml` says is on the canvas but this build
no longer produces (renamed, removed, or a sheet that lost a page). Publish with `root: out`,
`file_path: out/project/Index.dc.html`, and that map. Re-read the canvas first if it may have been
touched from the editor. Then run `python build.py published` and commit `published.yaml` — the next
build's removals are computed against it.

## Recipe schema

Sheets (`kind: sheet`, the default):

```yaml
code: CA-011                    # XX-NNN, unique across the library; must match the file name
status: standard                # draft | trial | standard | retired (see Recipe status)
name: Carrot cake cupcakes
cls: Cake · Cupcake, one bowl   # family · form, shown grey in the running head
lede: One sentence under the title.
source: NYT Cooking · Adapted, metric
contains: [Wheat, Milk, Egg, Nuts if added]
equipment: [12-cup muffin tin, Box grater]
key_figures:                    # exactly five; the last is usually the oven
- {label: Yield · cupcakes, value: '12'}
- {label: Oven · 350 °F, value: 175 °C}
uses: [FR-003]                  # optional; codes cited in formula rows/notes are found automatically
method_rail:                    # optional; one entry per method page (sub + notes in the left rail)
- {sub: Tick each step as done, notes: [Make FR-003 while the cupcakes cool.]}
method:
- {head: Prep., text: ≤ two lines on the sheet, time: —, target: 175 °C, target_f: 350 °F}
formula:
  basis: '% · flour = 100'
  notes: [† Doesn't scale in a straight line past 2×.]
  scale_by_pan: [[9 × 13 in, × 0.5], [Half sheet, × 1]]     # optional rail box
  scale_by_weight: true         # optional rail box; divisor computed from the total
  stages: [Biga, Primo, Secondo] # optional; rows then give g as a list per stage
  parts:
  - id: A
    name: Batter
    note: optional grey note after the part name
    outside: false              # true = "outside the formula", % shows —
    rows:
    - {name: All-purpose flour, g: 250, basis: true}    # basis rows sum to 100 %
    - {name: Carrot, note: grated, g: 250}
    - {name: Vanilla, g: —}     # "—" prints a dash; a list gives grams per stage; carry: true = → from the previous stage
    subtotal: {label: Batter}   # optional; grams are computed
  total: {label: Total batter}  # optional formula-wide total
schedule: {sub: ..., notes: [...], svg: BR-023-schedule.svg}   # optional
figures: {title: Figures, sub: ..., items: [{svg: BR-023-fig1.svg, label: Fig. 1, caption: ...}]}   # optional
done_when: [[Top, Springs back], [Inside, 96 °C]]
keeps: [[Room temp, 2 days], [Frozen, 1 month]]
fixes: {sub: Most likely cause first, label_width: 128, rows: [[Sunk middle, Underbaked; …]]}   # optional
trials: {sub: ..., columns: [Trial A, Trial B], rows: [{var: Date, values: ['', '']}]}   # optional
revisions:                      # newest last; Rev, date and "Last change" derive from the last row
- {rev: Rev 01, date: '2026-09-26', change: First issue, source: —}
revisions_blank: true           # the blank hand-written row under the table; false when the page is full
pages:                          # section order per page; method may be split with method:1-9
- [formula]
- [method, done_when, trials, revisions]
tent: {name: Carrot cupcakes, note: Contains nuts}   # optional staff-room tent card
```

Cards (`kind: card`): `code name yield keeps basis contains source formula: {rows, total} method note revisions`.
Card steps are one line of text plus `time` and `target`; keep the text under ~75 characters.

What the lint enforces: codes and file names agree, the family exists, five key figures, every
row has grams (or `—`), stage lists match the stage count, a flour basis has a `basis: true` row,
step heads end in a period, `pages` cover every method step exactly once, figure files exist,
revisions run 01, 02, … with ISO dates, cited codes exist.

## Conventions the renderer owns

- Percentages: one decimal, ROUND_HALF_UP; grams whole (1,221), `approx: true` prints ≈.
- Baker's percent per part when a part has a `basis` row, else formula-wide; `outside` parts print —.
- Ingredient daggers (†) sit right after the name, before the grey note.
- Multi-stage grids: the grey rule marks only the "Grams by stage" header group; body rows have no vertical rule.
- Cards with more than nine formula rows tighten row padding to 2 px (`dense: true` forces it).
- Canvas: one page per family, boards laid out one recipe per row, index on the default page.
- Index: rows grouped by family in library order, Linked = uses ∪ used-by, six blank "New entries" rows when they fit.
