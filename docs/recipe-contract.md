# Recipe contract, version 1

This is the shared data contract for human editors, Codex, Claude, and import/export tools.
`tools/schema.py` owns validation; do not implement a second validator in an agent guide.
The [README](../README.md#recipe-schema) contains the expanded YAML field examples;
[frozen examples](../tests/fixtures/README.md) exercise the renderer without depending on
changes to live recipes.

## Version and compatibility

Each recipe is a UTF-8 YAML mapping in `recipes/XX-NNN.yaml`. New recipes declare
`schema_version: 1` as an integer. Omitting it means version 1, so existing recipes need
no rewrite. Other values, including `"1"`, `true`, null, and future versions, are errors.
The version field never appears on a printed sheet.

Compatible optional fields can extend version 1. A change that alters the meaning of
existing data requires a new version, a documented migration, and explicit reader support;
never silently reinterpret an unsupported version. Recipe schema, JSON diagnostic report,
and preview record versions are separate contracts.

## Identity, status, and references

`code` is an uppercase two-letter family plus three digits, such as `BR-023`; it must
match the filename and a family in `library.yaml`. Codes are unique. `kind` defaults to
`sheet` and also permits `card`. `status` defaults to `standard` and permits `draft`,
`trial`, `standard`, and `retired`.

Drafts may appear on the website but never in the printed index. Trial and standard
recipes appear in both; retired recipes remain source records and are not rendered.
Preview accepts draft, trial, and standard recipes. Status changes are explicit source
edits; preview does not promote a recipe.

`uses` is an optional list of recipe codes. Codes in formula rows, components, and
variant rows also establish references; general method/source prose is not scanned.
Active recipes must not reference missing or retired recipes. A reference identifies
a separate recipe, not an instruction to inline its quantities into the parent formula.

## Fields and shapes

| Scope | Required fields | Optional fields and defaults |
|---|---|---|
| Sheet | `code`, `name`, `cls`, `lede`, `source`, `contains`, `key_figures`, `formula`, `method`, `done_when`, `keeps`, `revisions` | `schema_version: 1`, `kind: sheet`, `status: standard`; `equipment`, `uses`, `method_rail`, `pages`, `schedule`, `figures`, `components`, `fixes`, `trials`, `batch_log`, `variants`, `tent`, `dense`, `revisions_blank`, `foot`, `last_change` |
| Card | `code`, `name`, `yield`, `keeps`, `basis`, `contains`, `source`, `formula`, `method`, `revisions` | `schema_version: 1`, `kind: card`, `status: standard`; `uses`, `dense`, `formula_note`, `note` |
| Sheet formula | `parts`, each with `rows` | `basis`, `notes`, `stages`, `total: {label: ...}`, `scale_by_pan`, `scale_by_weight`; parts may have `id`, `name`, `note`, `outside`, `subtotal: {label: ...}` |
| Card formula | `rows` | `total` is the total label string |
| Ingredient row | `name`, `g` | `note`, `basis`, `dagger`, `approx`, `carry`, `total`, `outside`, `pct` (legacy override; prefer computed percentages) |
| Method step | `head`, `text` | `time`, `target`, `target_f`; sheets should include `time`, using `—` when unknown |
| Variant | `name`, nonempty `rows` | `note`, `steps` (list of short strings); container is `variants: {items: [...]}` with optional `title`, `sub`, `of`, `notes` |
| Revision | `rev`, `change` | `date`, `source`; absent/`—` dates are allowed, newest missing date warns |
| Tent | `name` | `note` |

`contains`, `equipment`, `uses`, rail `notes`, and variant `steps` are lists of strings.
Sheet `key_figures` is exactly five `{label, value}` mappings. Sheet `done_when` and
`keeps` are lists of `[label, text]` pairs; card `keeps` is a short string.
Row flags such as `basis`, `carry`, `dagger`, and `approx` are YAML booleans, not strings.
Legacy `notes: null` remains valid for empty rail/formula/schedule notes. Do not
generalize that exception to required containers or to `uses`, which must be a list.

Use explicit `pages` lists in reusable sheet examples. Each page is an ordered list of
sections: `formula`, `components`, `schedule`, `method`, `figures`, `done_when`, `fixes`,
`trials`, `revisions`, `batch_log`, `variants`. Split methods with `method:1-9` or
`method:10`. Cover each step once, in order; put done-when and revisions after the method.
Without `pages`, the renderer defaults to formula followed by method/done-when/trials/revisions.
See CONTRIBUTING for exceptions concerning trials and batch logs.

Revisions run `Rev 01`, `Rev 02`, and so on. Dates use `YYYY-MM-DD`. Preserve earlier
entries. Generated figure parameters and physical units are documented in
[`tools/figures.py`](../tools/figures.py); file-based SVGs live in `recipes/figures/`.
Typography, spacing, colors, and page dimensions belong to the templates.

## Quantities and computed values

Grams are finite, non-negative YAML numbers: `g: 250` or `g: 0.5`. Quoted numbers,
booleans, negative weights, NaN/infinity, ranges, and arbitrary text are invalid.
`g: —` means unspecified; put `pinch`, `1 pod`, or `as needed` in `note`. Do not invent
a numeric weight to pass validation. `approx: true` changes display only.

A sheet with `formula.stages` needs a `g` list on every row, with one entry per stage.
Entries follow the same numeric rules. `→` is permitted on `carry: true` rows. Cards
and variants use scalar quantities. Zero is a legitimate weight, not missing data.

The renderer derives percentages, totals, formatted grams, stage totals, scale divisors,
method numbers, revision headings, and cross-links. Never save derived underscore-prefixed
fields, `g_fmt`, or renderer output back into recipe YAML. Optional `pct` and row `total`
exist for legacy display controls; follow the examples instead of hard-coding arithmetic.

## Validation for people and programs

`python build.py lint` and `python build.py lint --json` use the same rules and exit
with 0 on success, 1 for invalid input. Warnings alone do not fail. Invalid CLI usage
exits with 2. Lint is strict about all recipes, including drafts; the build still skips
invalid drafts so an unfinished draft does not block unrelated live recipes.

JSON mode writes one object to stdout, with no progress text:

```json
{
  "report_version": 1,
  "schema_version": 1,
  "ok": false,
  "checked": 16,
  "diagnostics": [{
    "code": "FR-003",
    "file": "recipes/FR-003.yaml",
    "path": "formula.rows[0].g",
    "severity": "error",
    "rule": "quantity.invalid",
    "message": "Expected numeric grams; remove quotes around the weight."
  }]
}
```

The message above is illustrative; consumers must not parse its wording. Paths use
zero-based indexes; `$` means a document-level diagnostic. Files are repository-relative
for recipe diagnostics and may be absolute for loader failures. A load failure uses
`code: input`; `checked` is the number of recipes loaded, not a guarantee every rule ran
after a malformed structure. Syntax/load errors remain JSON in JSON mode. The current
lint combines field and semantic checks; it is not a general-purpose YAML type checker.

`rule` is an additive report-version-1 field; old reports may omit it. Consumers must
ignore unrecognized fields and provide a generic display for missing/unknown rules.
Existing field meanings and exit statuses remain unchanged. Rule identifiers are stable
categories, not permission to skip the message or assume every rule has a unique identifier:

| Rule | Meaning |
|---|---|
| `input.type` | Wrong container/scalar type or pair shape; repair the indicated field. |
| `schema.version` | Unsupported recipe version. |
| `quantity.invalid` | Invalid numeric quantity or placeholder. |
| `quantity.stage-count` | Expected a quantity list with one entry per stage. |
| `pages.range` | Malformed/out-of-bounds method range or range on another section. |
| `field.unknown` | Unrecognized field; severity determines whether it blocks. |
| `figure.invalid` | Missing/ambiguous diagram source, missing file, or bad generated geometry. |
| `recipe.invalid`, `recipe.warning` | General semantic error/warning; some older rules still use `$`. |

Structural guards cover common containers, list members, flags and method fields before
semantic traversal. A malformed recipe can stop its later semantic checks; other recipes
continue. Invalid library structure prevents dependent recipe validation. This is not a
complete validator for every optional nested field or an untrusted-upload service.
Unknown root keys warn and remain in source; unknown ingredient-row/variant keys remain
errors. A warning does not promise that a renderer or future editor preserves an extension.

Generated figures use finite positive numeric dimensions/scale and positive integer counts;
gap, frosting and thickness can be zero. Booleans and quoted measurements are not numbers.
Each figure item chooses exactly one `gen` or `svg`. Gauges have fixed physical scale;
neither gauges nor schematic folds accept `scale`. See [the diagram handbook](figures.md).

## Preview provenance

`python build.py preview CODE` validates, renders, fit-checks, and prints one recipe.
It writes PDFs, artboards, screenshots, and `preview.json` under `out/preview/CODE/`.
The record includes UTC generation time, recipe schema version, renderer version and
content hash, runtime versions, input fingerprint, and output hashes. Metadata stays
beside the printable output and never changes the sheet itself.

`python build.py preview-status CODE` exits 0 only when that record matches the current
inputs and its recorded output files are intact; otherwise it exits nonzero. Fingerprints
cover the parsed recipe, directly referenced recipes, referenced SVGs, library YAML,
renderer Python, templates, fonts, requirements, and key runtime versions. Recipe comments
and formatting alone do not invalidate the parsed-data fingerprint. The library and
renderer hashes are conservative: unrelated library metadata or renderer edits can mark
a preview stale. Hashes identify freshness; they are not a signature or a guarantee of
identical rendering on every operating system.

Rendering happens in a fresh staging directory. Validation, fit, print, and input-change
failures leave the last successful preview intact. During publication, the old directory
is retained as `.CODE.previous` until replacement succeeds; ordinary replacement failures
restore it. An interrupted replacement is recovered by the next `preview` or
`preview-status` run. Run one operation per recipe code at a time. No filesystem protocol
here promises survival of disk failure; recipe YAML and Git remain the source of truth.
