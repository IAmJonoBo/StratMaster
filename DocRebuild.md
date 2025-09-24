@workspace
Zero-pollution Docs Rebuild + Code Parity + CI hardening (behavior-preserving).

OBJECTIVE
Rebuild the documentation library from scratch to a clean, release-ready state; enforce Diátaxis; sync docs⇄code; remove planning junk (“sprint/phase/scope”); add automations so regressions are caught.

STRATEGY (safe rebuild)
1) Create branch `docs/rebuild-from-scratch`.
2) Scaffold fresh docs site in `docs.new/`:
   - If repo is JS/TS monorepo → Docusaurus preset classic with MDX support; else MkDocs + Material. Keep site local to repo (no external services).
3) Lay out Diátaxis structure:
   - `docs.new/tutorials/`, `docs.new/how-to/`, `docs.new/reference/`, `docs.new/explanations/` with landing pages and sidebars.
4) API reference regeneration:
   - TS libs: configure `@microsoft/api-extractor` + `@microsoft/api-documenter` OR `typedoc` to emit to `docs.new/reference/ts/`.
   - HTTP APIs: ensure `/openapi/openapi.yaml` (OAS 3.1). If missing, infer minimal spec from routes and create a draft; wire Redoc/Swagger UI page under `docs.new/reference/api/` with “build-from-spec” scripts.
5) Curate content (no pollution):
   - Inventory all `*.md|*.mdx` across repo. Move only product/user-facing material into `docs.new/` under Diátaxis categories.
   - Quarantine planning/backlog/sprint/phase/scope notes into `/internal/` (outside site). Remove from release path. Rewrite residual “sprint/phase” wording to neutral release language.
6) Parity sweep:
   - Cross-reference docs claims with code: public exports, CLIs, env/config keys, endpoints, and examples. Fix mismatches or open issues with TODO tags removed.
   - Regenerate code examples directly from working snippets wherever possible; flag any un-runnable snippets.
7) Quality gates:
   - Add and run: markdown lint (markdownlint/remark), spell-check (cspell), prose lint (Vale w/ Google/Microsoft rules), and link checker (lychee).
   - Add doctest/snippet verification strategy (prefer small runnable examples; for TS, verify via node/vitest where feasible; otherwise mark “non-executable”).
8) Wiring & build:
   - Ensure docs build locally from a clean checkout. Validate sidebar links, anchors, images, and versioned nav. Update top-level README to point to Tutorials / How-to / Reference / Explanations.
9) CI automations:
   - Create `.github/workflows/docs.yml` to run on PRs affecting docs/code: install deps; run api-extractor/typedoc; build docs; run markdownlint, cspell, Vale, lychee; fail on errors.
   - Create `.github/workflows/docs-rebuild.yml` (workflow_dispatch) to regenerate docs from scratch and open a PR via `peter-evans/create-pull-request`.
10) Finalise:
   - Generate `DOCS_REPORT.md` (changes, ToC, files moved/removed, parity gaps, open issues).
   - Open draft PR with `docs.new/` replacing old `/docs` on approval; preserve ADRs/SECURITY/CONTRIBUTING/LICENSE.
   - Don’t permanently delete any file without explicit confirmation.

DELIVERABLES
- New site in `docs.new/` following Diátaxis.
- Regenerated API references (TS + OpenAPI). Redoc/Swagger UI page.
- Linting configs: `.markdownlint*.json`, `.vale.ini` + styles, `cspell.json`, `lychee.toml`.
- CI: `docs.yml` + `docs-rebuild.yml`.
- `DOCS_REPORT.md` and updated `README.md`.

RULES
- No product behavior changes. Ask before any destructive change. Prefer small, reviewable commits. Show diffs and a checklist before PR.
