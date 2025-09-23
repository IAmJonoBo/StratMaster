# Open Questions

The following clarifications are required to proceed with high-confidence implementation of the frontier roadmap:

1. **Seed Corpus Definition**
   - What canonical documents (formats, size, licence) should be included in the demo/offline seed bundle? Existing seeds/fixtures cover limited scope.
2. **Model Allow-List**
   - Which OSS foundation models are approved for production (Mixtral, Llama 3, Nous-Hermes, Phi-3, etc.) and what licence constraints must be enforced per tenant?
3. **Usage Analytics Requirements**
   - Do stakeholders require anonymised usage analytics dashboards beyond existing Grafana metrics (e.g., retention, engagement) and if so what privacy thresholds apply?
4. **Expert Council Composition**
   - Confirm the list of disciplines and weighting schemes for the Expert Council MCP to avoid rework during PR-F.
5. **CI Budget**
   - What is the acceptable upper bound for CI runtime per push (minutes) to balance added eval/security jobs vs. developer productivity?

# Answers

Great—here’s a concrete decision package with ready-to-implement defaults for each of your five clarifications, plus how user-uploaded corpora slot into the plan. I’ve grounded the policy-sensitive bits (licences, privacy) in primary sources and solid guidance.

1) Seed Corpus (demo/offline bundle)

Goal. Ship a legally clean, high-signal seed so StratMaster works fully offline and showcases research → retrieval → reasoning → recommendations. Everything below is redistributable under permissive terms.

Recommended bundle (≤ 250 MB compressed):
	•	NIST AI RMF 1.0 core set (PDF + HTML snippets) — public domain; excellent for evidence badges and governance exemplars.  ￼
	•	W3C WCAG 2.2 excerpts (key success criteria + conformance tables) — allowed under the W3C Software & Document License; include attribution.  ￼
	•	GOV.UK Service Manual slices (service design, research methods, content design) — licensed OGL v3; include the OGL notice.  ￼
	•	HotpotQA small split (for multi-hop retrieval/evals) — CC BY-SA 4.0; package as a test/eval artifact with attribution.  ￼
	•	“StratMaster Canon” (we author baseline CEP/JTBD/DBA guides and rubrics) — license as CC BY 4.0 to keep redistribution simple; avoids pulling proprietary brand frameworks.

Why these? They cover accessibility, service/UX, AI risk governance, and give a robust multi-hop QA set for GraphRAG/EVALs—all under permissive terms or public domain. W3C has a permissive document license; NIST content is PD; GOV.UK is OGL v3. HotpotQA’s CC BY-SA is fine if we keep it quarantined as an eval dataset.  ￼

Packaging notes.
	•	Ship a seed manifest (provenance, licence, checksum).
	•	Keep HotpotQA under tests/evals/ to avoid mixing its SA terms with app docs.
	•	Provide a one-click online enrichment path (SearxNG + crawler) for tenants that enable web access; otherwise stay fully offline. (SearxNG is privacy-preserving by design when self-hosted.)  ￼

2) Model Allow-List (per-tenant policy)

Default “OSS-first” selections (production-approved, commercial use allowed):

Task	Models (primary → fallback)	Licence stance
Reasoning / Research	Mixtral-8x22B-Instruct → Qwen2.5-32B-Instruct	Apache-2.0 (Mixtral; Qwen2.5 except 3B/72B)  ￼
Edge / Low-resource	Microsoft Phi (3/3.5/4 family small variants)	MIT (Phi series)  ￼
Reranker / Embed	Qwen2.5-Reranker / E5 / BGE	Apache-2.0 (per model card)  ￼
Optional (policy-gated)	Llama 3.1 (8–70B)	Meta Llama Community Licence (not OSI); allow only if tenant accepts terms.  ￼

Explicit exclusions/notes.
	•	Nous-Hermes and other Llama-based fine-tunes inherit non-OSI terms or GPL overlays; do not enable by default.  ￼
	•	Qwen 3B/72B variants use the Qwen licence (stricter); keep them off unless legal approves.  ￼

Implementation. Encode per-tenant policy in configs/router/models-policy.yaml with deny-by-default and licence tags; the router enforces allow-list at call time.

3) Usage Analytics (privacy-preserving)

Ask: Do we need product analytics beyond Grafana/OTel?
Recommendation: Yes—ship anonymised, aggregated dashboards (retention, session length, feature adoption) with strict thresholds:
	•	No PII at source; apply de-identification (NIST IR 8053) and optional differential privacy for public/tenant-external reporting (NIST SP 800-226).  ￼
	•	Release thresholds:
	•	Suppress any cell with n < 10 (k-anonymity style).
	•	If DP is enabled, target ε ≤ 2 for external reports; document accuracy trade-offs (Census DP references).  ￼
	•	Storage/egress: metrics remain in-tenant; no third-party SaaS.
	•	Lineage: instrument events with OpenLineage/Marquez so every metric has data-provenance back to pipelines.  ￼

4) Expert Council (disciplines & weighting)

Disciplines (initial slate). Strategy; Behavioural Science; UX Research; Service Design; Visual Design; Communication/Brand; Growth/Marketing Analytics; Data Science/ML; Finance; Legal/Privacy; Accessibility/Inclusive Design; Localisation/Market Culture.

Weighting & adjudication.
	•	Start with equal priors; then learn per-discipline weights from retrospective accuracy on forecastable outcomes using Brier score (strictly proper) with calibration checks.  ￼
	•	For multi-rater judgements (e.g., critique labels), aggregate via Dawid–Skene (or Fast DS) to model rater reliability.  ￼
	•	Show confidence intervals and disagreement heat in the UI; down-weight experts that consistently under-perform on held-out validations.

5) CI Budget (per push)

Target: ≤ 12–15 minutes wall-clock per push on main pipelines; ≤ 10 minutes is the gold standard referenced in CI practice. Longer suites (evals, fuzzing, large end-to-end) run nightly. This keeps feedback tight without killing throughput.  ￼

Split the pipeline:
	•	Fast lane (≤ 6 min): lint, type-check, unit tests, licences/SBOM scan.
	•	Medium lane (≤ 9 min): integration tests with local services.
	•	Deferred lane (nightly): heavy EVALs, security DAST, flaky-test detector; keep flakes low (Google’s guidance on flaky tests).  ￼

⸻

User-Uploaded Corpora (training/seeding)

Capabilities (built-in):
	•	Parsers/OCR. Apache Tika + Unstructured for office/PDF/HTML; Tesseract/docTR for OCR; Camelot for tables; Trafilatura for boilerplate-free HTML text.  ￼
	•	Licence & provenance. Scan uploaded bundles with ScanCode Toolkit; attach licence findings + checksums to each document’s provenance.  ￼
	•	Privacy. Run Presidio PII detection/redaction prior to indexing.  ￼
	•	Lineage. Emit OpenLineage events on every ingestion → chunk → embed → index step (viewable in Marquez).  ￼

UX flow (wizard): Drop files → quick licence scan & PII preview → choose scope (project/tenant) → pick trainable vs. retrieval-only use → show estimated token/embedding cost → ingest.

Guardrails: Block high-risk licences from entering tenant-wide corpora (e.g., CC BY-SA except in tests/evals), unless the tenant explicitly whitelists them.

⸻

What to lock into the repo now
	1.	seeds/SEED_MANIFEST.yaml listing each seed artefact, licence, size, checksum, and provenance (URLs).
	2.	configs/router/models-policy.yaml prefilled with the allow-list above and licence tags (apache-2.0, mit, llama-community).  ￼
	3.	Analytics policy doc (docs/privacy/analytics.md) codifying k-anonymity≥10 and optional DP ε≤2 for external sharing, with links to NIST guidance.  ￼
	4.	Expert Council config (configs/experts/council.yaml) with the discipline list above and “Brier-scored learning” flag enabled.  ￼
	5.	CI matrix splitting lanes (fast/medium/deferred) and enforcing time budgets; add a flaky test watchdog.  ￼

⸻

Open items I’ll proceed on unless you object
	•	Generate the StratMaster Canon (CEPs/JTBD/DBAs) under CC BY 4.0 so we’re never blocked by third-party content.
	•	Build the ingestion wizard and licence/PII checks exactly as above.
	•	Set Mixtral/Qwen/Phi as defaults; gate Llama behind a toggle that surfaces the licence at enable-time.

If you want changes (e.g., include additional OGL sources or broaden the model list), say the word and I’ll amend the policies
