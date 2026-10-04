# Bench Sheets: six months of community expansion, then deepening

Roadmap · 3 October 2026 · First foundations implementation tracked in the
[work plan](foundations-implementation-plan.md) and [verification record](foundations-verification.md).

## Recommendation

Bench Sheet is a portable recipe record that turns quantities, method, and revision history into a consistent worksheet people can use at the bench.

Keep the recipe format and printed sheets as the core product. Expand the ways people can contribute, check, and edit them. AI should remain a useful authoring assistant; understanding the format, validating a recipe, and producing a sheet should not require a particular model, account, conversation, or application.

The first six months should establish a small, maintainable community around the existing repository. The next phase should deepen the capabilities that repeated use demonstrates are missing. A larger application is a possible consumer of the format, not a prerequisite for its survival.

This is a proposed sequence, not a delivery promise. Month 1 starts when the maintainer adopts the plan; an October 2026 start would put the six-month review in March 2027. Assume one maintainer with **2–4 hours per week**, occasional contributions, and no guaranteed volunteer engineering capacity. Keep only one substantial engineering change in progress. If participation stays small, complete the preservation and documentation work and defer the editor.

## Starting point and gaps

Inspected local baseline: `c98372bc3eb0e2c97326c7e60429a6569247cd22`. These observations describe repository contents, not a fresh rerun of its release checks.

| Existing strength | Gap to address |
|---|---|
| [Version-1 recipe contract](recipe-contract.md), numeric quantity rules, shared human/agent workflow | Some malformed structures still produce document-level diagnostics; lint is explicitly not a complete YAML type checker. |
| Selected-recipe previews, freshness records, recovery after ordinary replacement failures | Setup still requires Python and Chromium; preview operations for the same code must run sequentially. |
| [Frozen examples](../tests/fixtures/README.md), arithmetic and rendered-output regression tests | Four representative recipes are a useful starting corpus, not proof of support for every recipe or editor. |
| Templates, local fonts, static site, PDFs and source files | CONTRIBUTING still points to a design-system artifact on claude.ai. The design rules needed for maintenance should also live here. |
| Automated tests, fit checks and Pages deployment in [CI](../.github/workflows/check.yml) | Dependencies are pinned but runners/actions also change; PR builds and deployments currently share one concurrency group. |
| Contribution instructions and source credit conventions | No top-level project license, contribution templates, or explicit maintainer succession procedure was found. The font license covers the fonts, not the whole repository. |

The repo validates data and presentation. It does not establish that a recipe tastes good, has been cooked successfully, or has correct inferred conversions, storage guidance, or allergen information. Keep those kinds of evidence distinct.

## What must remain stable

1. **The sheet remains recognizable.** Preserve typography, physical sizes, visual hierarchy, section order rules, and readable type. Do not solve overflow by shrinking text. Deliberate design changes require an explained visual review.
2. **YAML remains the portable recipe source.** Humans and programs can use it without an account. Derived percentages and renderer internals do not become authored fields.
3. **Existing recipes retain their meaning.** Optional additions may extend version 1; semantic changes require a version decision, migration, and compatibility fixtures. Do not force a migration to ship an editor.
4. **One contract governs every author.** Human tools, Codex, Claude, and importers share validation and examples. Provider instructions stay thin pointers.
5. **Unknown information stays unknown.** No invented grams, inferred baking evidence, or silently discarded fields. Preserve source attribution and prior revision entries.
6. **The repository remains sufficient.** A future app must export usable source and assets. Printable output and a static browsing route survive the app's closure.

A format version, a renderer release, a recipe revision, and an application database version are separate concepts. Document their relationship; do not make them one version counter.

## Six-month delivery sequence

### Month 1 — Make the project maintainable by somebody else

**Deliverables**

- Bring the essential design-system specification into versioned repository documentation, with representative sheet/card/tent images and links to the actual template rules. Reconcile differences with the external artifact; record unresolved decisions rather than inventing them.
- Resolve licensing scope with the owner: code, documentation/design assets, contributed recipe material, and existing third-party assets. Record provenance and exclusions. Do not assign rights to sourced material merely because it is in the repository.
- Add a short maintainer guide covering setup, release, restore, dependency updates, review responsibilities, and how to pause maintenance. Document supported runtime versions and one fully tested setup route.
- Add three lightweight contribution forms: recipe correction/example, usability/bug report, and format/tool proposal. Each asks for a small reproduction or proposed use case, not a long essay.
- Publish a bounded contribution menu: reproduce setup, improve one error message, clarify one example, report one kitchen-use issue. Label which work needs cooking knowledge and which needs code knowledge.

**Exit evidence:** someone other than the author can find the design rules, produce a preview from a clean checkout using only repo instructions, and describe how to restore a saved release. Record their points of confusion. If no tester is available, mark independent onboarding unverified.

**Scope boundary:** no feature expansion is required to complete this month. License selection is an owner decision; this roadmap does not select or apply one.

### Month 2 — Make errors and contributions easier to review

**Deliverables**

- Improve validation at the input boundary for the most common failure shapes: null containers, wrong list/mapping types, invalid row flags, malformed method steps, and unsupported keys. Convert expected input failures into actionable diagnostics rather than tracebacks.
- Add stable diagnostic identifiers alongside the existing field paths before an editor depends on them. Decide and document report-version compatibility; consumers must never parse English messages.
- Reconcile README examples with the contract and workflow. Include a small complete valid recipe separately from the larger field reference, so users do not copy an intentionally partial example and encounter unexplained failures.
- Expand conformance fixtures by behavior: a sheet, card, staged carry, variant, reference, unspecified quantity, and malformed input. Reuse existing fixtures where they already cover the case.
- Separate PR verification concurrency from main-branch deployment concurrency. Review action/runtime maintenance, permissions and dependency-update procedure without creating a second build system.

**Exit evidence:** each selected invalid fixture produces a file/field/error identifier and useful repair guidance; supported legacy examples retain meaning and expected output; one contributor can reproduce a failed check locally. Unknown-field handling is explicit, including what remains a warning versus an error.

**Scope boundary:** better validation does not justify automatic correction of recipe facts or retroactive rejection of valid historical data without a compatibility decision.

### Month 3 — Run a small contribution and kitchen-use pilot

**Deliverables**

- Invite a small cohort through channels the maintainer chooses. Offer bounded tasks to cooks, technical contributors, and documentation reviewers. Participation is optional; no roadmap item assumes free labor.
- Test three journeys: print/use an existing sheet, revise an existing recipe, and add a recipe by adapting an example. Include a manual YAML editor and at least two available AI tools using the same instructions.
- Record setup time, assistance required, confusing fields, layout failures, and maintainer review time. Ask whether users return to the sheet, not just whether they like the idea.
- Keep kitchen observations linked to the exact recipe revision in an issue or small companion record. Record what was actually tried and under what conditions. A batch result is evidence for a proposed revision, not an automatic recipe edit.
- Triage reported trouble into documentation, validation, format limitation, or genuine authoring-interface need.

**Proposed learning target:** three independent participants, at least two returning for a second use or contribution, and five completed authoring/revision attempts across the group. These are planning thresholds, not research-derived proof of adoption. Report actual participation if the target is missed.

**Exit evidence:** a short findings document with the top three repeated obstacles, examples, and a decision about which single obstacle to tackle next. If people mainly struggle with setup, solve setup before building more recipe features.

### Month 4 — Test one narrow human editing route

**Preferred experiment, if the pilot supports it:** a local form that opens an existing supported recipe, edits a few common fields, validates it with the existing rules, and produces the existing preview. Start with ingredient quantities/notes and method text. Keep page planning manual initially.

Evaluate whether a small standalone interface or a bounded integration with existing work is cheaper to maintain. Do not create both. A form may use a local Python service; a completely browser-only port is not required and must not introduce a divergent validator.

**Required behavior**

- Show the source file, recipe code/revision, edited fields, and validation results clearly.
- Keep original bytes available. Cancel leaves them unchanged; save produces a reviewable diff and a recoverable copy. Detect externally changed source before saving.
- Preserve untouched supported data, array order, false/zero/empty values where meaningful, and authored precision. If an unsupported structure cannot be preserved reliably, disable saving and explain why. A read-only view is acceptable.
- State whether comments and formatting survive. Semantic preservation and exact text preservation are different promises.
- Avoid ambiguous edits: changing a weight may contradict an authored yield or key figure; show that discrepancy for review rather than silently changing prose.
- Validate and fit-check before labeling the preview current. A form save does not promote status or publish the site.

**Exit evidence:** two people can complete the supported edit without writing YAML or requiring an AI account; retained fields compare correctly; invalid/unsupported and concurrent-edit cases fail safely; representative PDFs pass visual review. Publish a support matrix, including exclusions.

**Fallback:** if there is no engineering capacity or editing is not the leading problem, deliver an improved guided CLI/documentation route and defer the form. This does not block the rest of the roadmap.

### Month 5 — Package releases and prove recovery

**Deliverables**

- Introduce tagged renderer/tool releases with change notes, supported environment, known limitations and migration notes when relevant. Keep recipe revision history independent.
- Define a complete portable bundle: recipe YAML, library metadata, referenced SVGs, templates, fonts/licenses, dependency information, and instructions. Include PDFs/static output for immediate reading where redistribution is permitted.
- From an independently unpacked bundle, regenerate a representative sheet and card and compare authored values and visual output. Explain which checks require installation/network access; shipped PDFs must remain readable without rebuilding.
- Review dependency updates in small batches with existing regression and visual checks. Pins aid repeatability but do not make software permanently maintainable or every OS render identically.
- Have another person execute the release/restore procedure if one is available. Record backup locations and ownership without putting credentials in the repository.

**Exit evidence:** a restore report identifies the bundle, renderer/runtime versions, checks performed, differences, and any unresolved dependency. Git history alone is not the entire backup plan; a PDF alone is not the editable recipe archive.

### Month 6 — Consolidate and decide what deserves depth

**Deliverables**

- Close or split stale proposals; finish maintenance work before adding a new capability.
- Turn successful pilot contributions into a small, attributed example collection. Prefer variety of supported structures and documented use over raw recipe count.
- Review repeated use, unsuccessful attempts, support burden, and second-maintainer readiness. Publish a short state-of-project note, including what will not be built next.
- Choose one deepening track below, or remain in maintenance mode. Ship a stable baseline and a contribution queue either way.

**Exit evidence:** an explicit next-phase decision names the user problem, evidence, responsible maintainer, acceptance boundary, and available time. Stars, downloads and impressive demos do not substitute for successful repeat use.

## Community operating model

Contributors propose changes; the maintainer remains responsible for compatibility and release decisions. A named backup reviewer is desirable, not an assumption. Keep discussions and decisions in repo-accessible records rather than private AI conversations.

| Contribution | Evidence expected before acceptance |
|---|---|
| Documentation or setup fix | Reproduced confusion or a walkthrough of the revised instructions. |
| Recipe correction or new example | Attribution, explanation of changed quantities/conversions, validation and preview; kitchen-use claims clearly identified. |
| Validator/renderer change | A failing behavior fixture or reproduction, compatibility assessment, relevant tests; visual review for changed output. |
| Format extension | At least two concrete use cases where existing fields fail, a minimal proposal, rendering semantics, compatibility and maintenance owner. Exceptions for urgent correctness fixes need an explicit explanation. |
| Editor or import adapter | Supported-field matrix, refusal/loss behavior, original-source retention, roundtrip fixtures, and a documented preview route. |

AI-assisted contributions use the same bar. Ask contributors to disclose uncertain transformations and what they verified; do not require a particular model or treat generated prose as evidence. Do not promise equivalent performance from all agents. Reproducible outcomes against shared fixtures are the useful measure.

Use a small queue, a monthly triage pass, and a realistic response expectation such as two weeks rather than an SLA. If review demand exceeds the maintainer's capacity for two consecutive months, pause new feature intake. Prefer accepting a few complete contributions over accumulating a large speculative backlog.

Before inviting uploads, explain that issues and this repository are public. Draft recipes currently also appear on the published site; `draft` does not mean private. Ask for permission before reusing participant photos or observations. Apply contribution rights guidance consistently, including to AI-assisted submissions.

## Phase two: deepen after six months

These are ordered options, not six parallel commitments. Select one primary track for the next roughly three months, review it, then choose the next. Months 7–12 are a planning horizon, not a promise to complete every track.

### A. Reliable authoring and integration core — default priority

Choose this if manual editing works but tools repeatedly lose information or duplicate logic.

Define a reusable parse → validate → derive → render boundary beneath the existing CLI. Keep authored input separate from mutable derived data. Specify version handling, diagnostics, supported types, asset resolution, and output ownership. Extend conformance examples before introducing a second implementation.

Acceptance: the CLI and one independent caller produce equivalent semantic results from the same corpus; caller input is unchanged; invalid documents fail consistently; upgrades have explicit compatibility coverage. If concurrent rendering is needed, add isolated jobs, locking/publication rules, cancellation and recovery tests before exposing a shared service.

Existing Proof integration is an investigation candidate, not assumed solved. A September 2026 local export experiment demonstrated a narrow unchanged-recipe roundtrip but found role loss after a quantity edit. Recheck the current implementation and resolve semantic transport and identity before advertising edited export. A correct-looking PDF alone does not prove an integration preserves the recipe.

That finding comes from the companion Proof repository's `docs/superpowers/specs/2026-09-28-canonical-export-feasibility.md`: changing yeast from 6 g to 5.1 g retained numeric quantities but lost hydration roles on re-import. It is dated local evidence, not a current compatibility certification or a dependency required to use Bench Sheets.

### B. Complete the human editing workflow

Choose this if the narrow editor is used repeatedly and its support burden is acceptable.

Add one demanded structure at a time: cards, variants, then stages/components where justified. Support a clear revision diff, recovery and export. Stable internal identities may be needed for reordered steps and page membership; do not put application UUIDs into printed labels or redesign the core merely to fit one database.

Acceptance: supported recipes survive open/edit/save/reopen with authored meaning intact, including meaningful absence and ordering; unsupported recipes cannot be silently flattened; users can leave the app with usable files. Keep advanced YAML editing available.

### C. More reliable page planning

Choose this if overflow or manual page layout is a leading recurring failure.

First improve diagnostics and suggest valid section moves. Only then consider an opt-in deterministic planner with explicit keep-together rules, method continuity, figure placement and manual overrides. Preserve existing explicit layouts.

Acceptance: every step appears once and in order; no clipped content or reduced type size; representative easy and difficult recipes receive visual review. Compare authoring effort with manual planning. Do not promise automatic layout for arbitrary recipe length.

### D. Reviewed import, followed later by photo/OCR input

Choose this if contributors repeatedly bring external recipes and manual transcription is the observed bottleneck.

Start with one structured input route, such as Schema.org Recipe or a documented export from another tool. Preserve the original and produce a field-level mapping/loss report. Stage imported content for human review, including conversions and inferred sections. Never silently make it a standard recipe.

For later OCR, show source image/crop beside extracted quantity, unit and instruction. Require confirmation of ambiguous numbers, fractions, temperatures and units; avoid treating provider confidence as factual correctness. Measure correction effort and consequential errors on a consented, representative sample before broadening support.

Acceptance: unsupported fields and uncertain transformations are visible; failure leaves the original accessible; review reduces transcription work in observed tasks. If correction takes as long as manual entry, stop expanding the importer.

### E. Revision-linked kitchen records

Choose this if repeated use produces observations people cannot reconnect to the right recipe.

Use optional companion records for actual yield, changes made during a batch, results and photos. Reference recipe code, revision and a content identifier. Keep observations distinct from the published formula and allow an explicit reviewed promotion into a new recipe revision.

Acceptance: someone can reconstruct which recipe was used and what differed; private observations stay out of public exports by default; the printable recipe still works without the records. Accounts, costing, inventory and business workflows remain separate product decisions.

## Measures and decision gates

Start a simple monthly ledger; no analytics service is required. Record attempts as well as successes, and distinguish maintainer-assisted completion from independent completion.

| Measure | Decision it informs |
|---|---|
| Clean setup success and assistance/time needed | Whether to improve installation before features. |
| Time to first valid, visually checked preview | Whether diagnostics or authoring controls are helping. |
| Repeat use/contribution after an initial attempt | Whether the workflow is useful beyond a demo. |
| Review minutes and unresolved support requests | Whether community growth is sustainable. |
| Failures by category: data, prose/layout, setup, tool loss | Which deepening track to choose. |
| Restore success and independent release completion | Whether the project can survive maintainer absence. |

Proceed to broader editing/import only with demonstrated repeat need, a bounded support contract, and an owner. Hold scope if evidence is thin. Stop a particular experiment if it requires silent data loss, erodes print readability, or creates more recurring work than it removes. These are proposed decision rules, not claims about future adoption.

If the project stays small, success can still mean a stable format, useful sheets, clear rights, reproducible releases, and occasional corrections. A documented maintenance pause, archived release bundle and transfer contact are better than promising a platform no one can maintain.

## First work packages

Implement these as small reviewable changes, in order; this document does not create issues or commit to all of them.

1. Repository-owned design specification and source-of-truth links.
2. Licensing/provenance inventory and an owner decision on redistribution and contributions.
3. Clean-setup walkthrough and one complete copyable example.
4. Contribution forms, bounded task menu, and maintainer/release guide.
5. Input-shape diagnostic improvements with compatibility fixtures.
6. CI concurrency/maintenance review and a restore-bundle exercise.
7. Pilot instructions and a small findings ledger.
8. A narrowly scoped editor experiment only after the pilot identifies that need.

The first four packages form a useful initial milestone even if no new application is built. They make Bench Sheets easier to understand, legally clearer to reuse once rights are resolved, and less dependent on its original author.

## Evidence and limits

The [research notes](community-roadmap-evidence.md) collect primary sources for portable recipe formats, contribution practices and loss-aware exchange. Existing projects demonstrate workable patterns; they do not establish demand for Bench Sheets or predict volunteer participation. The timeline, thresholds and priorities above are design judgments tailored to this repository.

No schema, renderer, recipe, CI setting, license, or published site is changed by this specification.
