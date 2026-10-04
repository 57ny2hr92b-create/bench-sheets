# Community roadmap evidence

Research date: 2026-10-03. Purpose: inform a six-month, community-assisted durability roadmap while preserving Bench Sheets' existing YAML and print format. These are primary-source observations and explicitly labeled proposals, not evidence of demand for this repository. Documentation describes capabilities; no cross-tool conversion or restore was executed in this research.

## 1. Human-readable files and machine interpretation can coexist

**Observed:** Cooklang defines recipes as plain-language text with annotations for ingredients, cookware, timers, and metadata. Its specification includes YAML front matter. It also warns that applications do not yet support every latest language feature. [Cooklang specification](https://cooklang.org/docs/spec/)

**Proposal:** Keep the current YAML authoritative and printable sheets useful on their own. Document a small, versioned contract and examples that people and different AI tools can follow. Consider Cooklang as a later interoperability target, not a reason to replace the existing format.

**Limit:** A readable format does not establish usability for this audience or reliable generation by any AI. Those need actual human trials and validation of generated recipes.

## 2. Shared semantics matter more than adding another serialization

**Observed:** Cooklang distinguishes its language specification from tool conventions. Its canonical metadata includes provenance (`source`, `author`), servings, yield, and preparation/cook time. Servings and yield have distinct meanings; image naming and location are also conventions. [Cooklang conventions](https://cooklang.org/docs/conventions/)

**Proposal:** Publish field meanings, examples, and rules for missing/unknown values before expanding the schema. Record a mapping table before attempting any adapter, especially for yield, units, ingredient references, provenance, and images.

**Limit:** Similar names do not establish equivalent semantics. Existing Bench Sheets fields require an explicit mapping and decisions about unsupported information.

## 3. Useful ecosystem tooling can be bounded

**Observed:** Cooklang's recipe CLI documents human-readable, JSON, YAML, Cooklang, Markdown, LaTeX, Typst, and Schema.org output choices. [Cooklang recipe command](https://cooklang.org/cli/commands/recipe/)

**Proposal:** An eventual single adapter or export command can connect to existing tools without building hosting, accounts, synchronization, or a whole recipe manager. Start with a narrow supported subset and fixtures.

**Limit:** Output format availability is not proof of round-trip fidelity, compatibility with Bench Sheets YAML, or print-layout preservation. Tool and format versions need testing at implementation time.

## 4. Contribution boundaries are part of maintenance

**Observed:** Open Source Guides recommends documenting project vision and processes, making scope explicit, keeping relevant decisions public, and declining contributions that do not fit. It treats issue and pull-request handling as substantive maintenance work. [Best practices for maintainers](https://opensource.guide/best-practices/)

**Proposal:** Publish accepted contribution types, deferred work, review expectations, and a realistic maintenance cadence. Welcome tested recipes, print feedback, reproducible bugs, and documentation improvements before broad feature development. Require discussion before major schema or product changes; define a pause policy rather than implying guaranteed support.

**Limit:** These are practice recommendations, not measured proof that a particular policy will attract contributors or reduce this maintainer's workload. Track actual review time and recurring burden.

## 5. GitHub can surface the contribution path without another service

**Observed:** GitHub recognizes contribution guidelines in the repository root, `docs`, or `.github`; it links them during issue and pull-request creation and on the contribution page. Issue and pull-request templates can communicate submission requirements. [GitHub contribution guidelines documentation](https://docs.github.com/en/communities/setting-up-your-project-for-healthy-contributions/setting-guidelines-for-repository-contributors)

**Proposal:** Use a short CONTRIBUTING file and focused templates before opening another community channel. Ask recipe contributors for source/permission information and evidence of cooking or print review; ask bug reporters for the input and observed result.

**Limit:** Discoverability is not participation. A community remains an experiment until people independently use the format and return useful feedback.

## 6. Code, recipe content, and third-party material need explicit scope

**Observed:** GitHub's Choose a License guidance permits different licenses in a mixed project when their scopes are explicit; documentation can use software or media licenses, and separately licensed documentation should clarify the treatment of code examples. Creative Commons says its licenses are applied by rights holders and does not recommend them for software. [Non-software licensing guidance](https://choosealicense.com/non-software/); [Creative Commons FAQ](https://creativecommons.org/faq/)

**Proposal:** State which license applies to code/templates, documentation, and contributed recipes/images. Establish provenance and contribution-permission expectations before accepting a shared recipe collection. Preserve attribution and exceptions rather than assuming a repository-wide notice grants rights to copied material.

**Limit:** These sources do not determine ownership or copyright status of any particular recipe, photo, or wording. No license was selected, changed, or applied by this research.

## 7. Import/export must report loss

**Observed:** Tandoor's documentation identifies concrete limitations: RecipeSage export omits images; Cooklang import accepts an individual `.cook` file but not attached images or ZIP input; its default import expects the exported ZIP rather than an extracted JSON file. Mealie nutrition import requires interpreting whether values are per serving or per recipe. [Tandoor import/export](https://docs.tandoor.dev/features/import_export/)

**Proposal:** Gate any adapter on sample recipes from real users, a supported-field matrix, explicit warnings for lost or ambiguous fields, preservation of original input, and round-trip checks where claimed. Never equate a successful parse with a faithful conversion.

**Limit:** These are Tandoor's documented integrations, not defects demonstrated in Bench Sheets. They justify examining loss modes; they do not establish which adapter this community needs.

## 8. Durable backups need a demonstrated restore

**Observed:** Tandoor distinguishes database and media backup, describes export/import as another backup route, and calls for checking imported recipes. Its documentation warns that copying a database directory depends on compatible restore conditions. [Tandoor backup documentation](https://docs.tandoor.dev/system/backup/)

**Proposal:** For this file-based repository, define a complete portable bundle containing canonical YAML, required assets, version information, instructions, and useful rendered output. Have a second person recover and render it in a clean environment. Keep print output as a useful fallback while retaining editable sources.

**Limit:** Tandoor's deployment details should not be copied into this simpler project. The general inference is to test recovery and include dependencies; this research has not verified a Bench Sheets backup.

## Decision implications (proposals)

Use the first six months to establish a documented contract, examples, contributor boundaries, licensing scope, reproducible rendering, and a demonstrated handoff/restore. Collect evidence of independent use, repeat use, conversion needs, contribution quality, and maintainer effort. Deepen only when a specific recurring problem has an owner, sample inputs, acceptance criteria, and an affordable support burden. A stable maintained format is a valid outcome; full SaaS, broad OCR, and many adapters are not required milestones.

No source above establishes market size, willingness to pay, likely adoption, or the right numerical gate. Any month-by-month milestones or thresholds in the roadmap are project choices to revisit against observed use.
