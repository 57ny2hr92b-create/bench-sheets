# Writing a Bench Sheet

The README says how the repo works. This file is the judgment: how to turn a recipe into a sheet
that is right at the bench. It is written for anyone — a person, or an assistant picking the repo
up cold — and it is the part that isn't enforced by the lint. Read it before writing `recipes/*.yaml`.

## The recipe

1. **Get the real recipe.** A technique article usually links to the recipe page; that is where the
   quantities are. Use the source's own gram values where it gives them. Convert the rest and list
   every conversion you made in the revisions note or the hand-over. Never invent a weight: an
   honest word (dash, pinch, 1 pod) goes as a grey `note` on the row with `g: —`.
2. **Rewrite the method in house voice.** Imperative, short, no "gently" or "simply". A step is a
   run-in head that ends in a period ("Fold.") and at most two lines of text — about 75 characters.
   Parameters go in the parameter column, not the text: `time` on line 1, `target` on line 2,
   `target_f` for a grey °F beside an oven or sugar temperature.
3. **Credit the source.** Author name when there is one; otherwise the publication
   ("NYT Cooking · Adapted, metric"). Invented recipes are "House formula · Original". After the
   dot: Original, Adapted, or Scaled ×n. Keep it short enough that Source · Contains · Last change
   stays on one line — the fit check will tell you.
4. **Invented recipes are checked, not guessed.** Anchor the ratios against two or three published
   recipes of the same kind and say which ones in the hand-over. Every figure you chose rather than
   sourced — a time range, a hydration estimate, a fix row — gets flagged.
5. **Keep the source's targets, note the common range.** If a source says 85 °C inside and most
   guides say 90–93 °C, print 85 °C and put the range beside it. Don't silently change it.

## Percent basis

Write it in `formula.basis` and flag the 100 % rows with `basis: true`. The lint requires a basis
row whenever the basis names flour.

- Flour carries the structure (nut flours count) → `% · flour = 100`. Flour improvers (vital wheat
  gluten, malt) get a % row but not the flag; say so in a rail note. Multi-part pastry (craquelin +
  choux) → each part flags its own flour; rail `% · each part's flour = 100`.
- No flour, one defining ingredient → anchor on it: `% · sugar = 100`, `% · whites = 100`,
  `% · milk + cream = 100` (flag both rows).
- No single anchor (ice cream bases, blends, brines) → `% of batch`, no basis rows; the renderer
  takes percentages from the total.
- A classic ratio exists → state it in a key figure too.
- Preferments and multi-stage doughs → `formula.stages: [Biga, Primo, Secondo]`, `g` becomes a list
  per stage, `carry: true` rows show the previous stage carried forward. Keep ingredient notes to two
  or three words in a stage grid or the names wrap.
- Parts outside the formula (pan butter, glaze, a coating) → `outside: true`; their % prints —.
- One base, several toppings or inclusions (focaccia, a snacking cake with swappable fruit) →
  keep the dough as the formula and put each option under `variants:`. A variant's header prints
  its total as a % of the formula total, its rows print their own internal %, and its `steps` say
  what changes in the method ("in on the third fold", "over the hot bread"). A variant that changes
  the dough itself (sugar in a sweet version) is a different recipe; give it its own sheet.
- Enriched doughs: the hydration key figure reads "Hydration · water / all" with both values
  ("49 / 62%"), counting yolks ≈ 50 % water, whole egg ≈ 75 %, milk ≈ 87 %; flag the all-liquid
  figure as an estimate.

## Format

- `kind: sheet` (Letter) for a recipe. `kind: card` (8 × 5 in) for a sub-recipe other sheets use —
  frostings, ganache, glazes, creams — cited by code from the sheets that use it. Reuse an existing
  card by code instead of rebuilding it. `tent:` on a sheet for a bake going out to people.
- Two pages is the norm. Past about 12 steps, or a recipe spanning two days, take three and split
  the method by day, not by page count: `pages: [[formula], [schedule, method:1-9, trials],
  [method:10-15, figures, done_when, fixes, revisions]]`. Balance the pages; a near-empty page 3
  usually means `fixes` belongs on page 2.
- **Sections read in bake order.** Nothing that judges the bake — Done when, If it goes wrong —
  comes before the last method step, and figures and variants sit beside the steps that point to
  them. Trials and the batch log are the exceptions — a chosen variable and a blank form judge
  nothing — so either may sit beside the day-1 steps to balance a long sheet. The lint refuses a `pages` list that breaks this; balance
  pages by moving trials or splitting the method, never by pulling a check above the steps.
- A card holds about 10 formula rows and 5 one-line steps. Past nine rows the renderer tightens row
  padding on its own; past that, move a row into a step or the card note.
- **A sheet gets a figure when its data implies one**, and the generators make that cheap:
  portions on a pan (cookies, rolls, meringues) → `gen: tray`; a slab cut into pieces (bars, focaccia,
  sheet cake) → `gen: cut`; layers with stated heights (layer cakes, tiramisu, tarts) → `gen: section`;
  dough rolled to a size or folded → `gen: dimensions` or `gen: fold`; anything portioned by eye →
  `gen: gauge` at actual size. Nothing else gets one — a Bundt, a loaf, a plain cookie sheet do
  without, and an even grid the yield already states ("half sheet, 4 × 4") can stay words when the
  sheet is full; a cut map earns its space when the cut isn't obvious (mixed sizes, an order that
  matters, a sling to lift by). Put the figure beside the steps it illustrates (a section beside the assembly steps), never
  after the checks. One figure usually; two at most, side by side, sharing a height and fitting 520 px
  together — if they don't, keep the one that adds more. Vocabulary: solid = edges, dashed 3/2 = fold
  or cut, arrow = movement, ticked = dimension, 45° hatch = filling, sparse stipple = crumb.
  Imprecision only on edges that are imprecise in life (a spread frosting), never on anything measured
  against. Hand-draw in `recipes/figures/` only what the generators can't (a schedule, a hang, a
  temperature curve, shaping frames), starting from an existing SVG.

## Numbers

- Grams only in the YAML. Percentages, subtotals, totals, the scale-by-weight divisor and the
  index are computed. Don't type them.
- °C rounds to the nearest 5 (325 °F → 165 °C; 110 °F water → 45 °C; 84 °F proof → 30 °C).
  °F appears only for oven and sugar-cook targets, in grey, in key-figure labels and `target_f`.
- Open-ended cues get ranges. "Until cool" stays as the `time` and the typical range goes in
  `target` ("4–12 h"). Never replace a cue with a bare time, and never print a single number where
  the honest answer is a range. Flag ranges you supplied yourself.
- Scale by pan on interior area, not nominal size: 8 × 8 in ≈ 64 in²; 9 × 9 ≈ 81; 9 × 13 ≈ 117;
  half sheet ≈ 204 (× 1.75 of a 9 × 13); quarter sheet ≈ 9 × 13; 20 cm round ≈ 49; 23 cm round
  ≈ 64. State the piece count at each factor; a different depth changes the bake time.
- Ingredients that don't scale in a straight line past 2× — leavening, extracts, spices, tea —
  get `dagger: true` and the standard † rail note.

## House altitude

The test kitchen is at about 4,700 ft (Idaho Falls). Water boils near 95 °C, which weakens hot
infusions and lowers the boil in custards. Candy targets drop 2 °F per 1,000 ft. Cakes at this
altitude: leavening −12–25 %, sugar −0–12 %, liquid +12–25 %. Yeasted doughs proof faster. Put
altitude notes in the formula rail and run them as a trial before changing the sheet; if a sheet
is written with altitude already applied, say so in the rail and give the sea-level figures.

## Revisions and status

- `revisions:` runs Rev 01, 02, … newest last. The running head, "Last change" and the index Rev
  all derive from the last row. Earlier drafts get rows even when their changes weren't recorded
  ("Second draft (changes not recorded)", date —). Never edit or delete an older row.
- `status`: `draft` while writing (renders to `out/drafts/`, prints to PDF, never reaches the site
  or index); `trial` once it's in the binder to be baked; `standard` when it's the house version;
  `retired` instead of deleting. Never delete a recipe file.
- Any new live row or Rev change bumps `index.rev` and `index.date` in `library.yaml`.

## When it doesn't fit

`python build.py check` fails on any section past 968 px (448 on a card), a three-line step, a
wrapped ingredient name, or an overflowing meta row. Fix by writing, in this order: shorten the
step or the note; move a section to the next page in `pages:`; move a rarely-used part (pan
butter) into a rail note; `revisions_blank: false` on a full page; `dense: true` on the sheet;
`fixes.label_width`. Never shrink type or padding — those belong to the design system. If a recipe
needs something the templates can't express, extend `templates/` and `tools/schema.py` in the
same commit and add a fixture test, rather than working around it with prose in a field.

## Design system

Black text, one grey (#5C5C5C) for labels, hairline rules (#BDBDBD), IBM Plex Sans 400/500/600,
nothing below 12 px, no color, fills, shadows, rounded corners, photos or drawings of food.
Sections hang in a 152 px left rail; content keeps one left edge. Percentages one decimal
(half-up) in grey 400; grams whole in black 500 — weight and percent must never be mistaken for
each other. The templates implement all of this; the spec they follow is the Bench Sheet design
system (README, tokens and component previews), kept as a Design System artifact on claude.ai.
