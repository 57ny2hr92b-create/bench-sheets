# Bench sheets

Bench Sheet turns a recipe into a consistent, print-ready kitchen worksheet with checked
quantities and a clear method, so people can bake from it reliably and different AI tools
can edit it without losing its structure.

The test-kitchen recipe library as data. Each recipe is one YAML file; `build.py` renders every
Bench Sheet, component card and tent card, the library index, the PDFs, and a static site that
GitHub Pages serves from every push to `main`. The site is the binder: edit YAML, push, done.

```
recipes/            one file per recipe, named by code (BR-023.yaml). This is the record.
recipes/figures/    SVG figures and schedules, referenced by file name
library.yaml        families, index rev/date
templates/          Jinja2 templates that own the Bench Sheet markup
tools/schema.py     lint (runs before every build)
tools/figures.py    figure generators (tray, cut, section, dimensions, fold, gauge) for `gen:` figure items
tools/fit.py        Chromium fit check with the real IBM Plex Sans
fonts/              IBM Plex Sans 400/500/600 woff2, vendored (OFL) so builds never fetch
tools/import_dc.py  one-off importer for hand-built artboards (how the first six got in)
tests/              pytest regression suite
out/                build output (ignored by git)
```

`CONTRIBUTING.md` is the judgment side — how to write a recipe well (basis, voice, ranges, altitude,
what to cut when a page is full). Read it before writing a YAML file.
Its [shared editing workflow](CONTRIBUTING.md#shared-editing-workflow) applies equally to
people, Codex, and Claude. See the [versioned recipe contract](docs/recipe-contract.md)
and [runnable examples](tests/fixtures/README.md) for reusable data and checks.

## Setup

```
pip install -r requirements.txt
python -m playwright install chromium           # for `check`, `pdf`, `site`
```

## Everyday commands

| Command | What it does |
|---|---|
| `python build.py list` | Every recipe in the repo — code, status, kind, name — drafts and retired included. Run it before scaffolding a new one. |
| `python build.py lint` | Validate every recipe. Errors name the file and the field. |
| `python build.py lint --json` | The same strict check, including drafts, as one JSON diagnostic report. Exits 1 on errors. |
| `python build.py build` | Lint, then render `out/project/*.dc.html` and `Index.dc.html`. |
| `python build.py check` | Build, then render every artboard in Chromium and fail if anything overflows, a step runs to three lines, an ingredient wraps, or the meta row breaks. Screenshots land in `out/shots/`. |
| `python build.py new CA "Olive oil cake"` | Scaffold `recipes/CA-012.yaml` with the next free code. |
| `python build.py next-code BR` | Just print the next free code. |
| `python build.py site` | Build, print every live recipe and draft to PDF, and write `out/site/` — `index.html` (IX-00 with links, then a Drafts list), one page per recipe and tent, `pdf/`. This is what Pages serves. |
| `python build.py pdf [CODE …]` | Print `out/pdf/CODE.pdf` (all pages of a sheet; tent and cards as their own files at their own size). No codes = every live recipe. |
| `python build.py preview CODE` | Validate one recipe, render and fit-check all its pages (drafts and tent cards included), then print its PDFs under `out/preview/CODE/pdf/`. No site build or publication. |
| `python build.py preview-status CODE` | Check whether the saved preview matches current inputs and its output files are intact. Exits 1 if missing or stale. |
| `python -m pytest -q` | Regression tests (math, links, rendering, fit). |

## Previewing one recipe

Run `python build.py preview SV-001` while editing a draft. It validates that recipe,
renders its artboards, checks every page in Chromium, and prints a PDF only after
the fit check passes. Screenshots are in `out/preview/SV-001/shots/`; artboards are
beside that folder. The command accepts exactly one code (case-insensitive).

An invalid draft or an overflowing page exits with an error instead of being skipped.
Unknown and retired codes are rejected. A failed run leaves the previous successful
preview unchanged; use the success message to identify a newly generated PDF.
Unrelated recipes are not linted, though the library YAML files must still parse.
The ordinary `check` command continues to check the live binder; use `preview CODE`
to check a draft. The preview never changes recipe status, the index, or the site.

Each successful preview includes `preview.json` with a UTC generation time, input and
renderer fingerprints, runtime versions, and output hashes. Run `preview-status CODE`
before sharing an older PDF. The record stays off the printed pages. Failed publication
restores the previous preview; an interrupted replacement is recovered on the next
preview/status run. Run one operation per recipe code at a time.

## Recipe status

Every recipe has a `status`: `draft` → `trial` → `standard` → (`retired`).

- **draft** — rendered and on the site with its own page and PDF, listed under **Drafts** below the index page and marked "draft", but never on the printed IX-00. Lint errors on a draft are reported and the draft is skipped; they never block the build. New recipes scaffold as drafts.
- **trial** — on the site and in the index, marked "· trial" in the Format column.
- **standard** — the default when the field is absent; the binder.
- **retired** — kept in the repo as the record (history, revisions, cross-links from old sheets still resolve in git), not rendered, not indexed. Retire rather than delete.

## Adding a recipe

1. `python build.py list` first: a draft is listed on the site under Drafts but not on the printed index. Then `python build.py new <FAMILY> "<Name>"` — families are `BR PA CA CK CF CR FR GA` (see `library.yaml`; add a family there before using a new prefix).
2. Fill in the YAML. Grams only; percentages, subtotals, totals, the scale-by-weight divisor, step numbers, Rev/date in the running head, index rows and cross-links are all computed.
3. Set `status: trial` (or `standard`) when it's ready for the site; leave it `draft` while you work — `python build.py pdf CODE` prints a draft too.
4. `python build.py check`. Fix whatever it flags — shorten a step, move a section to the next page in `pages:`, drop the blank revisions row (`revisions_blank: false`). Don't shrink type or padding; those are the design system's.
5. Bump `index.rev` and `index.date` in `library.yaml` (any new row or Rev change is a new index rev).
6. Commit and push. The `build` workflow lints, tests, fit-checks, and deploys the site. A red X on GitHub means a page no longer fits or a recipe fails lint; nothing is deployed until it's fixed.

## Revising a recipe

Append a row to `revisions:`. Never edit or delete an older row — the running head, the "Last change"
line and the index Rev all derive from the newest row, and the older rows are the history. Bump the
index rev in `library.yaml`.

## The site (GitHub Pages)

One-time setup: repo Settings → Pages → Source: **GitHub Actions**. After that every push to `main` that passes the checks deploys `out/site/`. Each recipe page shows its sheet pages at true size (scaled to fit on a phone), with PDF and Print links; the index page is IX-00 with every code linked. IBM Plex Sans is vendored in `fonts/` (OFL) and served by the site itself; the PDFs embed the same files.

## Recipe schema

New recipes declare `schema_version: 1`; existing files without it also mean version 1.
Unsupported versions fail validation. See the [contract](docs/recipe-contract.md) for
compatibility rules, structured diagnostics, and preview provenance.

Sheets (`kind: sheet`, the default):

```yaml
schema_version: 1              # omitted in legacy files = version 1
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
  scale_by_weight: true         # optional rail box; divisor computed from the total. Reads "g dough ÷ n = g flour";
                                # a string names the basis (sugars); {basis: sugars, of: batch} names both words
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
figures: {title: Figures, sub: ..., items: [{svg: BR-023-fig1.svg, label: Fig. 1, caption: ...}]}   # optional; items sit side by side, below: true starts a new row (an actual-size figure beside a tray won't fit)
                                # or generate one: {gen: tray|cut|section|dimensions|fold|gauge, ...} — see tools/figures.py; tray and gauge take oblong pieces as [length, width] mm
# a figure item may be generated instead of drawn: give it gen: and its parameters (all mm), no svg:
#   {gen: tray, pan: half, cols: 4, rows: 3, piece: 45, spread: 90, label: Fig. 1, caption: ...}
#   {gen: cut, pan: 9x13, cols: 6, rows: 4, sling: long, ...}   pans: half quarter 9x13 8x8 9x9 9x5, or size: [w, h]
#   {gen: section, layers: [[sponge, 25], [filling, 8], [sponge, 25]], frosting: 4, width: 120, ...}
#   {gen: dimensions, width: 300, height: 200, thickness: 5, ...}
#   {gen: fold, kind: letter, ...}                          letter | book | single
#   {gen: gauge, diameters: [30, 40, 50], ...}              actual size, 5 cm check bar
# tools/figures.py holds the generators; scale: overrides the default px per mm.
done_when: [[Top, Springs back], [Inside, 96 °C]]
keeps: [[Room temp, 2 days], [Frozen, 1 month]]
fixes: {sub: Most likely cause first, label_width: 128, rows: [[Sunk middle, Underbaked; …]]}   # optional
trials: {sub: ..., columns: [Trial A, Trial B], rows: [{var: Date, values: ['', '']}]}   # optional
variants:                       # optional; named sub-formulas laid over the main formula (toppings, inclusions, finishes)
  title: Variants               # rail title (default Variants); sub defaults to "Each as % of dough weight"
  sub: Toppings · each as % of dough
  of: dough                     # the word after "% of" on each variant head: dough (default), batter, base
  notes: [Two variants on one pan → halve each.]
  items:
  - name: Kalamata and rosemary
    note: optional grey note after the name
    rows:                       # same row keys as the formula; g only — each row's internal % and the
    - {name: Kalamata olives, note: 'pitted, halved', g: 120}   # variant's % of the formula total are computed
    steps: [One-line notes, ≤ ~60 characters, shown beside the rows]   # what changes in the method
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
row has finite, non-negative numeric grams (or `—`), stage lists match the stage count, a flour basis has a `basis: true` row,
step heads end in a period, `pages` cover every method step exactly once, figure files exist,
revisions run 01, 02, … with ISO dates, cited codes exist, every variant has a name and rows with grams, every `gen:` figure renders,
`pages` reads in bake order and places done_when and revisions.

Quantity rules apply to sheets, component cards, variants, and every entry in a stage
list. Write `g: 250`, not `g: "250"`; quoted numbers, booleans, negative weights,
infinity/NaN, ranges, and arbitrary text are errors. Use `g: —` for an unspecified
quantity and put words such as `pinch` or `as needed` in `note`. A staged formula
requires a list with one entry per stage; `→` is permitted only on `carry: true`
rows. `approx: true` controls display and does not relax validation. Error messages
include the recipe code and a zero-based field path, for example
`formula.parts[0].rows[1].g`.

## Conventions the renderer owns

- Percentages: one decimal, ROUND_HALF_UP; grams whole (1,221), `approx: true` prints ≈.
- Baker's percent per part when a part has a `basis` row, else formula-wide; `outside` parts print —.
- Ingredient daggers (†) sit right after the name, before the grey note.
- Multi-stage grids: the grey rule marks only the "Grams by stage" header group; body rows have no vertical rule.
- Cards with more than nine formula rows tighten row padding to 2 px (`dense: true` forces it).
- Index: rows grouped by family in library order, Linked = uses ∪ used-by, six blank "New entries" rows when they fit.
