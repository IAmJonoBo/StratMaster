# Open Questions

All previously raised clarifications have been answered by stakeholders. The responses below should be treated as implementation-grade requirements and reflected across the sprint plan, gap analysis, and blueprint diffs.

## 1. Seed Corpus Definition *(Resolved)*
- **Answer**: The offline/demo bundle must ship 24 canonical artefacts covering PDF (8 strategic memos), DOCX (4 playbooks), XLSX (4 financial scenario models), CSV (3 experiment logs), PPTX (3 board decks), HTML (2 competitive briefs), and 2 scanned TIFF image sets for OCR validation. All materials must be sourced from StratMaster-owned content or Creative Commons BY 4.0/MIT-compatible publications. Target compressed size ≤ 500 MB with SHA-256 manifest and provenance metadata mirroring the existing `demo-ceps-jtbd-dbas.json` schema.
- **Implication**: Extend `seeds/` to include binary fixtures plus manifest, ensure ingestion/eval tests cover every format, and document packaging/downloading steps in the developer quick start.

## 2. Model Allow-List *(Resolved)*
- **Answer**: Approved default OSS models are: Mixtral 8×7B Instruct (Apache-2.0), Llama 3 8B Instruct (Llama 3 community license), Nous-Hermes 2 7B (Apache-2.0), and Phi-3 Medium Instruct (MIT). Providers must route through vLLM or Ollama with quantised gguf variants available for offline mode. Any additional models require tenant-specific legal review and opt-in configs.
- **Implication**: Lock router/model configs, retrieval rerankers, and performance tables to this set and document licence handling + per-tenant override process.

## 3. Usage Analytics Requirements *(Resolved)*
- **Answer**: Product leadership requires privacy-preserving usage analytics beyond existing Grafana metrics. Minimum metrics: daily active workspaces, completion vs. fallback counts, evaluation gate pass rates, and average end-to-end latency. Data must be aggregated at workspace/day granularity with k-anonymity ≥ 5, differential privacy noise on counts, and retention capped at 30 days. PII is prohibited; only hashed workspace IDs may be stored.
- **Implication**: Incorporate ClickHouse/Parquet sink or reuse Postgres rollups with privacy guards, surface dashboards in Grafana, and add CI checks ensuring analytics collectors honour redaction policies.

## 4. Expert Council Composition *(Resolved)*
- **Answer**: Council disciplines and base weights are: Strategic Leadership 0.20, Organisational Psychology 0.15, Service Design Research 0.15, Communications Strategy 0.15, Brand Science 0.15, and Economics & Pricing 0.20. Decisions require ≥ 0.72 weighted quorum. Ties are broken by Strategic Leadership unless overruled by combined Communications + Brand Science > 0.35 weight objection.
- **Implication**: Encode weights/doctrines in configs, expose dissent rationale in UI, and align MCP tooling + UX copy accordingly.

## 5. CI Budget *(Resolved)*
- **Answer**: The engineering org caps per-push CI runtime at 20 minutes (hard ceiling 22 minutes). Heavier eval/security sweeps should run on nightly schedules with cached artefacts. Fast-fail lint/type/test gates must finish within 12 minutes on the reference GitHub-hosted runner.
- **Implication**: Optimise workflows (caching, matrix fan-out), stage heavyweight jobs asynchronously, and document expected runtimes in DX guides.
