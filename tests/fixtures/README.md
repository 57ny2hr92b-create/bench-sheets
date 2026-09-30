# Runnable recipe examples

These frozen examples are independent of the live recipe library. Copy their structure,
then use `python build.py new FAMILY "Name"` for a fresh code and revision history.
They are examples of the data format, not a claim that a recipe has been kitchen-tested.

| Example | Demonstrates |
|---|---|
| `recipes/CA-011.yaml` | A two-page sheet, ingredient notes, a component reference, and a generated figure |
| `recipes/BR-023.yaml` | A three-stage dough, carry rows, subtotals, SVG figures and schedule |
| `recipes/FR-003.yaml` | A compact component card with a flat formula |
| `recipes/BR-024.yaml` | Variants, a three-page method, generated figure, and a tent card |

Source: upstream commit `6d61e1e`; the staged example shortens the vanilla note from
`1 pod, aromatic` to `1 pod` so its ingredient cell fits. The live recipe is untouched.
The accompanying library and referenced SVGs are frozen with the recipes.

Run `python -m pytest -q tests/test_examples.py` to validate the examples, check known
arithmetic, compare every rendered artboard with the original renderer, and measure fit
in Chromium. The ten hashes in `artboard-sha256.json` were captured with the upstream
renderer before the durability changes. They protect exact printed markup, including
typography and page structure. A renderer change that intentionally alters that output
requires visual review of all affected pages before updating the corresponding hashes.
Keep template changes and baseline updates together and explain the visual change.

The examples omit `schema_version` to exercise legacy compatibility; new recipes emitted
by the scaffold declare `schema_version: 1`. Both use the same version-1 contract.
