# Reuse and provenance: decision record

**Owner decision pending.** The owner requested recommendations before choosing. This document grants no new license and establishes no ownership.

## Inventory

| Material | Current evidence | Remaining work |
|---|---|---|
| Python, templates, tests | Versioned source; no top-level license at baseline | Confirm rights holders/contributors and choose software terms. |
| Documentation/design descriptions | Repo Markdown; earlier external Claude artifact | Confirm ownership and content-license scope. |
| Recipes/frozen examples | Source/revision fields, including third-party adaptations | Review individual origins and permissions; attribution is not a redistribution grant. |
| Authored SVG/imported HTML | `recipes/figures/`, `tools/originals/` | Identify third-party material before blanket licensing. |
| Generated gallery | Figure engine plus fixture catalog | Decide code/design coverage; generation does not settle rights. |
| IBM Plex fonts | [SIL OFL 1.1 and IBM notice](../fonts/LICENSE) | Preserve existing terms/notices. |
| Dependencies | Pinned names in requirements | Their own licenses remain applicable. |

## Options for the owner

**Recommended for broad reuse:** MIT for owned code/templates, CC BY 4.0 for owned narrative documentation/design material, with explicit recipe/asset exclusions until reviewed. MIT permits commercial reuse and distribution with required notices; changes need not be published. CC BY permits sharing/adaptation including commercial use with attribution and other stated conditions. [MIT](https://choosealicense.com/licenses/mit/), [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).

**Alternative for reciprocal sharing:** MPL 2.0 for owned code, CC BY-SA 4.0 for owned narrative/design material. MPL requires availability of covered source files/modifications when distributed under its conditions while allowing larger works under other terms. CC BY-SA requires shared adaptations to use the same or compatible terms. This adds downstream obligations. [MPL 2.0](https://choosealicense.com/licenses/mpl-2.0/), [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).

Neither ensures maintenance or grants rights to somebody else's material. Decide code and content scopes separately. This inventory makes no recipe-specific legal determination. Before applying terms confirm rights-holder names, exclusions, contribution permissions and example coverage, then add the actual license files. Until then do not label the whole repository MIT/CC or all recipes freely redistributable.

## Contribution provenance

Record source/author/link, changes, conversions/inferred values and permission basis for submitted wording/assets. Preserve earlier credits and revisions. AI assistance does not supply rights or verify a source. Resolve unclear redistribution before merging; use a minimal reproduction or description where a full source cannot be shared.
