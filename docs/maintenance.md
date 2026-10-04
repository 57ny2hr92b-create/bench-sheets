# Maintaining and handing on Bench Sheets

Start with [quickstart](quickstart.md), [contract](recipe-contract.md), [design](design-system.md) and [diagrams](figures.md). AGENTS and CLAUDE point to these shared rules. No previous AI conversation is required.

## Review and release

Keep one substantial format/renderer change in progress. Review a small queue monthly; there is no support SLA. Welcome reproducible bugs, docs, attributed corrections and representative examples. Discuss new fields/generators first. Generated contributions require the same review as manual ones.

Recipe changes need lint, a current preview and visual review, an appended revision, and an index revision/date bump for live changes. Automated checks are not kitchen testing. Renderer changes need:

```sh
python -m pytest -q
python build.py lint
python build.py check
python build.py site
```

Inspect a staged sheet, card, variant/tent and affected diagrams. Record known failures; do not refresh baselines just to pass tests. Publication is explicit: a push/merge to `main` can deploy Pages. Check both build and deployment jobs afterward. Local checks are not deployment evidence.

For a tool release record commit/tag, runtime/browser/dependency versions, compatibility decisions, visual changes, verification and limitations. Recipe revisions remain separate. Tagged releases are proposed practice, not a claim that historical tags exist.

## Portable archive and restore

Include recipes and their SVGs, library metadata, Python tools, templates, fonts/licenses, requirements, tests and docs. Include PDFs/static output for immediate reading where redistribution permits. Review [rights/provenance](reuse-and-provenance.md) before distributing bundles.

For committed source:

```sh
git status --short
git rev-parse HEAD
git archive --format=tar.gz --output=../bench-sheets-source.tar.gz HEAD
```

The archive includes **committed files only**, not uncommitted changes, ignored previews or Git history. Keep a separate Git backup when history matters. Store source, reading copies, environment inventory and checksums in two owner-controlled locations. Keep credentials/personal records out of the repo.

Restore into a fresh directory. Install requirements/browser, run tests/lint, then preview FR-003 and BR-024. Compare quantities, revisions, diagrams and page structure with saved reading copies. Record differences and downloads required. Pins do not lock every transitive dependency or guarantee identical PDF bytes across OS versions.

[Verification evidence](foundations-verification.md) distinguishes a local restore exercise from independent onboarding. Do not describe it as offline installability or a second maintainer's readiness.

## Maintenance and succession

Review dependency/actions updates periodically in small batches. Recheck representative output after browser/font changes. Preserve schema meanings or provide explicit migrations.

CI selects Ubuntu 24.04 and pins official action releases by commit, with version comments.
This avoids an automatic switch to a different Ubuntu release or a moved action tag;
the hosted image still receives updates. Review action runtime requirements and upstream
release notes when updating those pins. PR checks exercise build/artifact upload; the
main-only deployment action also needs verification when publication is authorized.

If maintenance pauses, leave a last verified release, known limitations and a way to propose takeover. Keep repository/domain/archive ownership in an owner-controlled record and arrange a backup maintainer when someone accepts. No backup maintainer is assumed. A stable format is worthwhile without a hosted service.
