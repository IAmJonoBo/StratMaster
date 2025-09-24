@workspace
Docs ⇄ Code Parity + Diagrams + Sanity Checks (release-prep, behaviour-preserving)

CONTEXT
The docs scaffold is rebuilt. Populate it with accurate, code-verified content and diagrams; remove planning artefacts; update root docs; keep to Diátaxis.

PLAN
1) Inventory & map
   - Build an inventory of public APIs (HTTP, CLI, modules), env/config keys, routes, adapters, and exported TS types.
   - Detect monorepo layout (apps/, libs|packages/) and ensure doc paths match the structure.

2) Populate Diátaxis
   - Classify every page into Tutorials / How-to / Reference / Explanations; create missing pages and index entries.
   - For each API/CLI/config: generate or update **Reference** pages from source (TypeDoc or API Extractor + API Documenter for TS; OpenAPI for HTTP).
   - Ensure **Tutorials/How-to** contain runnable, minimal examples; mark any non-executable snippets clearly.

3) Diagrams (add where they help understanding)
   - Add **Mermaid** diagrams inline for flows, sequences, states, and data journeys in tutorials/how-tos.
   - Add **C4 diagrams** for architecture (Context/Container/Component) using **Structurizr DSL** checked into /architecture; export PNG/SVG to /docs/reference/architecture.
   - Link diagrams from affected pages; keep them close to the code they explain.

4) Parity & sanity checks
   - Cross-reference every claim/example against code: imports compile, commands run, endpoints exist, env vars documented with defaults and security notes.
   - Convert TODO/TBD/PLACEHOLDER to either (a) minimal feature-flagged scaffolds (off by default) or (b) GitHub Issues linked from docs.
   - Run clean install → typecheck → lint → unit/e2e → build; fix any doc/code mismatch surfaced by builds/tests.

5) Root docs refresh
   - Update README entry points to Tutorials / How-to / Reference / Explanations; add quickstart and support/contact.
   - Ensure CONTRIBUTING, SECURITY, CODE_OF_CONDUCT, and SUPPORT exist and are current; link from README.
   - Create/refresh CHANGELOG in **Keep-a-Changelog** format; confirm **SemVer** usage in version badges/examples.

6) Quality gates (add if missing; run now)
   - Prose/style: Vale with Google/Microsoft styles; spelling: cspell; Markdown: markdownlint; links: lychee.
   - API docs: regenerate TypeDoc or API Extractor → API Documenter; regenerate OpenAPI and re-render (ReDoc/Swagger UI).
   - Validate all internal/x-ref links and sidebar routes; fail CI on broken links or style violations.

7) Deliverables
   - Branch `docs/flesh-out-parity`.
   - Updated `/docs/**` content with diagrams; `/architecture/**` (Structurizr DSL) + exported images.
   - Refreshed root docs (README, CONTRIBUTING, SECURITY, CODE_OF_CONDUCT, SUPPORT, CHANGELOG).
   - `DOCS_REPORT.md` listing: pages added/rewritten, diagrams added, mismatches fixed, issues created, remaining gaps.
   - Draft PR with diffs + checklist. Ask before deleting any file; move planning artefacts to `/internal/`.

RULES
- Preserve behaviour; small, reviewable commits. If uncertain, propose options in DOCS_REPORT first.
