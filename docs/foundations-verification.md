# Foundations work: verification and remaining decisions

2026-10-03. Local branch `codex/durable-format-foundations`, based on `c98372bc3eb0e2c97326c7e60429a6569247cd22`. Scope: [implementation plan](foundations-implementation-plan.md), first two months of the roadmap. This work does not implement the community pilot or promise that two months of independent use have occurred.

## Work completed

- Repository-owned design reference, illustrated diagram handbook, quickstart, maintenance/restore guide, provenance inventory and licensing options.
- Three contribution templates and a PR evidence template. README/CONTRIBUTING link the shared documentation; no separate agent-specific rules were introduced.
- Input guards and additive structured diagnostic categories in the existing validator, including recipe/library containers, flags, bounded method ranges and figure sources. No new recipe version or alternate validator.
- Geometry validation, deterministic catalog tests and ten standalone SVG examples covering six generator families. Fold output no longer contains a duplicate `fill` attribute; existing browser behavior used the first, black value, which is retained.
- PR/main concurrency isolation and deployment-only Pages/OIDC permissions in the existing CI workflow.

## Evidence recorded during implementation

Environment: macOS arm64, Python 3.13.13, repository-pinned requirements, Playwright 1.56.0 and installed Chromium build 1194. CI targets Python 3.12; this local run does not replace a hosted run or certify every Python/OS combination.

- Before changes: **104 tests passed** in a fresh temporary environment. A previous temporary environment lacked pytest; it was not reused for verification.
- After the first implementation pass: **185 tests passed**; all **40 live/index artboards** passed the fit check. All **46 nonretired recipe artboards**, including drafts/tents, matched the captured baseline markup hashes exactly.
- Independent review identified missing nested `rows`/`items` guards, mixed-type unknown variant keys, and overflowing derived geometry. Reproducing tests failed first; fixes passed the focused suite (**89 tests**).
- Gallery outputs were parsed as XML, checked for standalone namespaces, and compared with their generator inputs. Seven non-fold examples retain pre-change SVG bytes; three folds differ only by removal of the duplicate attribute. Gauge tests verify circle radius and the 50 mm check bar in CSS pixels.
- Visually inspected the complete generated diagram gallery, FR-003 card, and BR-024 first sheet page/tent. No clipping observed in those views. Physical printing/calibration and cooking were not performed. Book/single folds retain the existing schematic drawing; this is not a new technique-validation claim.
- A separate source archive was extracted outside the checkout. It included working changes explicitly (a normal `git archive HEAD` would not); the restored copy generated all BR-024 pages and the tent PDF successfully. It used the already installed environment/browser, so this is source portability evidence, not an offline installation or independent-person test.

Final post-review verification: **193 tests passed in 42.85 seconds** from the independently
restored source tree. Its 107 source files were hash-checked against the working-copy inventory
before that run (subsequent edits only completed these documentation records). The first restored
run exposed a regression in simultaneous unknown-key/missing-row reporting; that was corrected
without weakening the original test, then the full suite passed. Current-library JSON lint reports
16 recipes with no diagnostics. The local site build generated 13 live recipes, 2 drafts and 23 PDFs.
All 46 recipe artboard hashes still match baseline. Local Markdown links, issue-template headers,
workflow YAML structure and `git diff --check` passed. Hosted CI/deployment was not run.

## Deliberate compatibility decisions

### Hosted follow-up

On 2026-10-03, the exact committed `dd0e971` source archive passed its SHA-256 check,
all 193 tests (45.56 seconds), and lint for 16 recipes after extraction into a new directory.
[PR #2](https://github.com/57ny2hr92b-create/bench-sheets/pull/2) was then opened.
Its [first hosted run](https://github.com/57ny2hr92b-create/bench-sheets/actions/runs/37174510973)
passed all 193 tests on Python 3.12/Linux (58.47 seconds), the live fit check, the site build,
and artifact upload. Deployment was skipped as intended for a PR.

That run reported Node 20 action deprecations and the scheduled migration of `ubuntu-latest`.
The workflow now selects Ubuntu 24.04 and pins official Node 24-compatible releases:
[checkout 7.0.1](https://github.com/actions/checkout/releases/tag/v7.0.1),
[setup-python 7.0.0](https://github.com/actions/setup-python/releases/tag/v7.0.0),
[upload-artifact 7.0.1](https://github.com/actions/upload-artifact/releases/tag/v7.0.1),
[upload-pages-artifact 5.0.0](https://github.com/actions/upload-pages-artifact/releases/tag/v5.0.0),
and [deploy-pages 5.0.1](https://github.com/actions/deploy-pages/releases/tag/v5.0.1).
Release commits and action inputs/runtimes were checked against their official repositories.
See the PR checks for verification of this workflow revision. Actual deployment remains
unverified until a separately authorized merge/publication.

### Format compatibility

Keep schema/report versions at 1. Diagnostics add `rule` without changing existing fields; clients must accept unknown fields/rules and older reports without `rule`. Root extensions warn; row/variant typos remain errors. Historical explicit null note lists retain their empty-note meaning. No recipes, template files or frozen artboard hashes were edited.

Strict geometry rejects quoted/bool/nonfinite/negative measurements and invalid counts; these are invalid authored geometry under the documented numeric contract. Folds/gauges reject ignored scale overrides. This is a local authoring tool, not a resource-bounded service for hostile input; trusted SVG assets still require review. Optional schema coverage is improved, not exhaustive.

## Remaining work, in order

1. Owner selects licensing scopes/rights-holder names after reviewing [the options](reuse-and-provenance.md). No new license was applied.
2. Reconcile the historical external design artifact if it becomes available; the new reference accurately describes the checked-in implementation rather than claiming to reproduce an unseen artifact.
3. A new contributor independently tries setup/edit/preview. Windows instructions still need environment verification; Python 3.12/Linux is now covered by hosted CI. No second-maintainer readiness is claimed.
4. Review the PR's current checks, and verify deployment only when publication is requested. A passing PR build does not exercise the deployment action.
5. Continue type/semantic coverage from actual reports; build a supported-field matrix before exposing an editor/importer. Arbitrary imports/OCR and automatic page planning remain later work.
6. Trial release tagging, independent restore, archive ownership and backup-maintainer handoff with an actual participant. Local source recovery is a first step.

An existing content discrepancy was visible during inspection: FR-003's authored yield says approximately 385 g while its computed ingredient total prints 388 g. It was left unchanged because this work preserves recipe content. It illustrates why valid data and good page fit do not establish that every authored statement agrees with the formula; a future recipe correction should receive its own revision/review.

Publication status: feature branch pushed and PR #2 opened; no merge, license application or live-site deployment performed.
