# PR Checklist (Feature Flags Off by Default)

Before requesting review, confirm the following with all new feature flags left at their default `false` value:

- [ ] Environment audit: verify no `ENABLE_*` flags introduced by roadmap work are set in local `.env` or CI configuration.
- [ ] Linting: `make lint`
- [ ] Core tests (installs editable packages and runs pytest): `make test`
- [ ] Fast developer tests (runs pytest against local sources): `make test-fast`
- [ ] Optional advanced suites (run when touching corresponding areas):
  - Retrieval benchmarks: `make test.advanced` (ensures benchmark helpers stay healthy)
  - Contract/load testing: `make test.contract` / `make test.load`
- [ ] Documentation build (if docs changed): `mkdocs build`
- [ ] Update relevant ADR/RFC references and ensure new feature flags default to `false` in configuration templates.

Attach logs for the required commands above when submitting the PR.
