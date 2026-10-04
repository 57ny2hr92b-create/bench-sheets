# Diagrams and figures

Bench Sheets generates technical SVG diagrams from YAML without AI. Six generators live in [tools/figures.py](../tools/figures.py). Authored SVG files cover schedules and techniques outside those generators. Both routes use the same sheet layout and preview workflow.

## Add a diagram

Add a `figures` block to a sheet, then place `figures` in the appropriate page's section list beside its method:

```yaml
figures:
  title: Figures
  sub: Portion spacing
  items:
  - gen: tray
    pan: half
    cols: 4
    rows: 3
    piece: 45
    spread: 90
    label: Fig. 1
    caption: Portion before baking; dashed circles show expected spread.
```

Lengths are **millimetres**, counts integers. Geometry is authored, not inferred from weights. `label` and `caption` belong to presentation; `below: true` starts a new figure row. Two figures must fit the 520 px content width together or use separate rows/pages. Run `python build.py preview CODE`, inspect its PDF/screenshots, then `preview-status CODE`. Valid SVG may still be too wide or misleading.

## Generator reference

| `gen` | Required geometry | Options/defaults |
|---|---|---|
| `tray` | `pan` or `size`; `cols`, `rows`, `piece` | Round diameter or oblong `[length, width]`; round `spread` defaults to piece; `gap` packs portions centrally instead of distributing cells; `scale: 0.5` px/mm. |
| `cut` | `pan` or `size`; `cols`, `rows` | `sling: long` or `short`; `first_cuts: true` labels first cuts when both counts are even; `scale: 0.5`. |
| `section` | `layers: [[kind, height], ...]`, **bottom to top** | `width: 120`, `frosting: 0`, `scale: 1.6`. |
| `dimensions` | `width`, `height` | `thickness: 0` omits edge view; `scale: 0.5`. Thin edges draw at least 3 px for visibility; the label is the measurement authority. |
| `fold` | None | `kind: letter` (3 layers), `book` (4), `single` (2). Schematic three-frame illustration; no physical scale control. |
| `gauge` | Nonempty `diameters` or `oblongs` | Round diameters and/or `[length, width]` pairs; fixed 96/25.4 px/mm; no scale override. |

Named pan interiors (mm): `half` 430×300, `quarter` 300×215, `9x13` 330×230, `8x8` 203×203, `9x9` 229×229, `9x5` 229×127. These are conventions, not guarantees about your equipment. For a measured pan use `size: [width, height]`, omitting `pan`; a recognized name takes precedence if both are given.

Section kinds: `sponge`, `cake`, `savoiardi` stipple; `crust` dense stipple; `filling`, `cream`, `curd`, `jam` hatch; `glaze`, `ganache` black; `plain` outline. This vocabulary draws texture, not ingredients.

Tray `gap` is the pre-bake edge gap. Round dashed spread may overlap; the diagram is not a proof of baked fit. Oblongs use length/width/gap rather than round spread semantics.

## Executable examples and gallery

[The catalog](../tests/fixtures/figures.yaml) covers every generator, both portion shapes and all folds. Images below are generated from it; do not hand-edit them.

| Example | Diagram |
|---|---|
| Round tray | ![Round tray](assets/figures/tray.svg) |
| Oblong tray | ![Oblong tray](assets/figures/tray-oblong.svg) |
| Cut map | ![Cut map](assets/figures/cut.svg) |
| Section | ![Cross-section](assets/figures/section.svg) |
| Dimensions | ![Dimensions](assets/figures/dimensions.svg) |
| Letter fold | ![Letter fold](assets/figures/fold-letter.svg) |
| Book fold | ![Book fold](assets/figures/fold-book.svg) |
| Single fold | ![Single fold](assets/figures/fold-single.svg) |
| Round gauge | ![Round gauge](assets/figures/gauge.svg) |
| Oblong gauge | ![Oblong gauge](assets/figures/gauge-oblong.svg) |

Regenerate from the repository root:

```sh
python - <<'PY'
from pathlib import Path
import yaml
from tools.figures import render
out = Path('docs/assets/figures')
out.mkdir(parents=True, exist_ok=True)
for name, spec in yaml.safe_load(Path('tests/fixtures/figures.yaml').read_text()).items():
    svg = render(spec).replace('<svg ', '<svg xmlns="http://www.w3.org/2000/svg" ', 1)
    (out / f'{name}.svg').write_text(svg, encoding='utf-8')
PY
```

Markdown may resize images or substitute fonts. This gallery is **not a calibrated print surface**.

## Actual-size gauges

Print the recipe PDF at **100% / actual size**, without fit-to-page. Measure the 5 cm check bar on paper before using a gauge. Phone displays, browser views and screenshots do not establish physical size. If a gauge is too wide, use fewer shapes or another page; never shrink it.

## Authored SVG and schedules

Store SVGs in `recipes/figures/`, reference their basenames, and place their sections in `pages`:

```yaml
figures:
  title: Figures
  items:
  - svg: BR-023-fig1.svg
    label: Fig. 1
    caption: Hang after baking.
schedule:
  sub: Two-day process
  notes: [Start with the first mix.]
  svg: BR-023-schedule.svg
```

These are existing panettone examples, not generic instructions. See the [drawing](../recipes/figures/BR-023-fig1.svg) and [schedule](../recipes/figures/BR-023-schedule.svg). Adapt only when the technique applies.

Use explicit dimensions/viewBox, descriptive `aria-label`, local geometry, shared marks, and text at least 12 px at intended output size. SVG is embedded as markup: these are trusted repository assets, not sanitized uploads. Review scripts, event handlers and external resources before accepting authored files. A public importer needs a separate sanitization boundary.

## Limits and extensions

There is no automatic schedule, temperature curve, kneading, shaping or freehand generator. Use reviewed authored SVG. New generators need a repeated use case, clear units, invalid-input checks, deterministic examples and visual/fit review. Existing valid output stays stable unless a correction is explicitly recorded.
