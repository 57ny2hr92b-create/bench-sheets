# Durable format foundations implementation plan

> For agentic workers: use `superpowers:executing-plans` task by task. The user requested sequencing followed by autonomous execution in this session. Track evidence and remaining decisions below.

**Goal:** Make the existing format inheritable, easier to author, and explicit about diagrams without changing its printed design.

**Architecture:** Preserve the YAML → shared validator → deterministic renderer → checked preview path. Documentation describes the current implementation; input guards improve that same validator. No new app, second schema implementation, or format version.

**Tech stack:** Python, PyYAML, Jinja, Playwright/Chromium, pytest, Markdown and GitHub Actions.

**Spec:** [Community expansion roadmap](community-expansion-roadmap.md), months 1–2, plus the user's explicit requirement to preserve and explain existing diagram generation.

## Constraints and decisions

- Keep templates, live recipe quantities, source history and frozen artboard baselines unchanged.
- Keep recipe schema version 1; JSON diagnostics gain an additive `rule` field, with existing fields retained. Document that consumers ignore unknown fields.
- Preserve unknown root fields as warnings, not new hard failures; existing unknown ingredient/variant fields remain errors. Do not promise complete schema coverage.
- Make licensing inventory and options explicit; do not select a license without owner intent.
- Work in the current checkout on `codex/durable-format-foundations`, keeping the two existing roadmap documents. No push, merge or publication in this task.
- Derive local design documentation from checked-in templates and instructions. The original Claude artifact is not available here; do not claim a verbatim migration or reconciliation.
- Calendar-dependent independent onboarding/community feedback stays pending; local verification cannot substitute for another user's experience.

## Review focus

1. Malformed nested YAML should identify the field, continue checking other recipes, and not crash preview/build.
2. Zero, false, unknown quantity markers and valid historical data must retain their meaning.
3. Generated diagrams must reject nonfinite/negative geometry and malformed counts instead of producing misleading SVG or exceptions.
4. Diagrams must remain deterministic; gauges retain their physical calibration and diagrams remain usable without AI.
5. Docs/examples must be runnable; restoration must include assets/fonts, not only recipe text.

## Task 1 — Preserve design and authoring knowledge

**Files:** `docs/design-system.md`, `docs/figures.md`, `docs/quickstart.md`, `docs/maintenance.md`, `docs/reuse-and-provenance.md`, `README.md`, `CONTRIBUTING.md`, `.github/ISSUE_TEMPLATE/*.md`, `.github/pull_request_template.md`.

**Interfaces:** consumes existing templates, figure generators, contract and CLI; produces a linked local handbook and contribution route, no runtime changes.

- [x] Document physical dimensions, typography, section order, layout budgets, exceptions and source-of-truth boundaries.
- [x] Document every generator and authored SVG route, parameters, units, calibration, fitting, examples and limitations.
- [x] Add short first-preview instructions, a complete copyable example using a frozen card, and maintenance/recovery steps.
- [x] Inventory rights/provenance; prepare decisions without assigning licenses.
- [x] Add small contribution templates and link the new docs from README/CONTRIBUTING.
- [x] Check local links, compare documented values with source, execute example and restore steps.

## Task 2 — Make malformed data actionable

**Files:** `tools/schema.py`, `build.py`, `tests/test_input_shapes.py`, `docs/recipe-contract.md`.

**Interfaces:** retain `Lint.err/warn(code, msg, path='$', file=None)` compatibility; add optional `rule`. Add structural guards before existing semantic lint. Keep `schema.run(lib, recs, figs_dir, quiet=False)` and CLI behavior.

- [x] Add regression cases for malformed formula/parts/rows, method, booleans, pages/ranges, figures and library; assert exact paths, structured rules, no mutation, and continued checks of another recipe.
- [x] Watch tests fail on the current validator, then implement guards and additive diagnostics.
- [x] Preserve existing quantity/version behavior; test generic versus specific rule identifiers and unknown-root warning policy.
- [x] Run focused and complete regression suites; document the supported diagnostic contract and remaining limitations.

## Task 3 — Preserve diagram generation as a supported capability

**Files:** `tools/figures.py`, `tests/test_figures.py`, `tests/fixtures/figures.yaml`, `docs/figures.md`, generated `docs/assets/figures/*.svg`.

**Interfaces:** preserve `figures.render(spec) -> str`, raising `FigureError` for invalid generator input. Retain valid existing output.

- [x] Create a small example catalog covering all six generators, oblong variants and the three folds; capture existing output hashes before changes.
- [x] Add tests for deterministic well-formed SVG and calibrated gauge geometry, plus invalid values/counts/pairs/kinds. Watch invalid-input tests fail first.
- [x] Validate inputs before geometry; normalize expected errors to `FigureError` without changing valid SVG. Ensure generated fold SVG is well-formed; if existing malformed markup requires correction, record the exact exception to byte preservation.
- [x] Generate repository-owned gallery assets from that catalog; validate XML and visually inspect representative renders.
- [x] Run full regression and live fit checks. Do not silently regenerate frozen recipe baselines.

## Task 4 — Maintenance checks and handoff

**Files:** `.github/workflows/check.yml`, this plan, `docs/foundations-verification.md`.

**Interfaces:** same CI build/deploy jobs; isolate concurrency by event/ref, grant deployment permissions only to deployment.

- [x] Separate PR runs from main deployment cancellation; preserve PR verification and main-only deployment.
- [x] Run clean-environment tests, lint, fit checks and representative previews; compare all live rendered markup to the starting branch.
- [x] Verify restore from an independently copied source bundle and record environment/evidence.
- [x] Obtain a fresh review, fix substantive findings, and retain a clear outstanding-work list.
- [x] Leave a reviewable local branch with documentation and results; do not publish.

## Execution record

- Baseline commit: `c98372bc3eb0e2c97326c7e60429a6569247cd22`.
- Initial reused temporary Python environment lacked pytest; create a fresh temporary venv with pinned requirements before judging tests. This is an environment issue, not a baseline test failure.
- Owner confirmed: preserve the current print/YAML direction for people, AI and future apps. Prepare licensing recommendations for a later owner decision.
- Baseline: 104 passing tests; captured all 46 nonretired recipe artboard hashes before edits.
- Task 1: documentation/contribution/provenance work complete locally; historical artifact reconciliation, independent onboarding and final license selection remain explicitly pending.
- Task 2: field guards/diagnostics implemented. Preserved null note lists found in historical sources and simultaneous variant error reporting protected by the original tests.
- Task 3: all six generators documented; ten gallery SVGs and three design snapshots retained. Geometry/physical-scale/XML checks added. Only fold duplicate-attribute markup corrected; no live recipe artboard changed.
- Task 4: fresh review completed; all three reported issues addressed with reproducing tests. Final verification and remaining external decisions are recorded in [foundations verification](foundations-verification.md).
- Ruling: use a local feature branch in the existing checkout so the existing roadmap drafts stay together; do not alter or publish main. No worktree cleanup is needed.
- Ruling: source-recovery exercise includes explicitly inventoried working changes, unlike `git archive HEAD`; installed runtime/browser reused, so do not claim offline installation or independent-user verification.
