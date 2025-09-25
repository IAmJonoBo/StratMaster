@workspace
BRIEF: Build an adaptive “Orchestration & Decision OS” for StratMaster that plans, debates, decides, and wires improvements across code, docs, UX, AI, and ops—end-to-end, platform-agnostic.

OBJECTIVE
- Create a lean, high-leverage system that (1) turns strategy into shippable work, (2) stress-tests decisions with structured debate, and (3) continuously measures outcomes and refactors the codebase to keep the system fast, reliable, and intelligent.

OPERATING PRINCIPLES (embed as checklists in /orchestration/.kernel/)
- Delivery performance: track DORA metrics (deploy freq, lead time, change failure rate, MTTR). Gate merges on regression. [doc links in NOTES]
- Reliability: define SLIs/SLOs + error budgets; alert on golden signals only (latency, traffic, errors, saturation). Block risky rollouts via canaries. 
- Decision hygiene: run ACH matrices + pre-mortems for major changes; log all choices with ADRs.
- Strategy cadence: map value chains (Wardley), classify context (Cynefin), and iterate tight OODA loops to adapt plans quickly.
- AI governance: apply NIST AI RMF controls (risk, bias, transparency) to any agentic or ML feature. Fail closed.

SCOPE — IMPLEMENT THESE MODULES
1) Debate Engine (/orchestration/debate/)
   - Implement Analysis-of-Competing-Hypotheses (ACH) and Pre-Mortem workflows with templates + CLI.
   - Add “constitutional critique” and self-consistency rounds for AI proposals before they touch code.
   - Emit machine-readable verdicts (JSON) for pipelines to consume.

2) Decision Log (/docs/architecture/adr/)
   - Enforce ADRs for every material decision; wire a lint that blocks PRs without an ADR reference.
   - Provide MADR template and index; auto-link ADRs to code diffs and issues.

3) Strategy Mapper (/orchestration/strategy/)
   - Wardley map skeletons + scripts to render/update maps from a service catalog.
   - Cynefin triage checklist for each initiative; route to appropriate playbooks (probe-sense-respond for complex, etc.).
   - OODA loop annotations on roadmaps; require “next observe/orient checkpoint” metadata.

4) Planning Engine (/orchestration/planning/)
   - Converts strategy items → epics → thin vertical slices; supports modular-monolith + hexagonal ports/adapters boundaries.
   - Event-storming stubs to define domain events; generate pub/sub contracts and message schemas.
   - Data contracts for shared datasets; validate in CI.

5) Experimentation & Insight (/orchestration/experiments/)
   - Turn feature ideas into tests: A/B (with sequential testing to avoid peeking), CUPED variance reduction, guardrails metrics.
   - Add causal inference notebook templates (DoWhy/CausalML) for post-experiment learning; export uplift reports.
   - RAG/LLM evals: add ragas jobs; block deployment on factuality/grounding thresholds.

6) AI Orchestration (/orchestration/agents/)
   - Provide a minimal multi-agent runner (e.g., LangGraph/AutoGen/CrewAI) for code/​docs tasks with tool use + human-in-the-loop gates.
   - Register tools for repo ops (search, refactor, tests, docs build), design exports (diagrams), and experiment management.
   - Enforce safety rails: sandboxed PRs, unit/integration/e2e checks, and governance checklist before merge.

7) Developer Platform Hooks (/backstage/ or /platform/)
   - Expose golden paths via templates: service, job, experiment, ADR, doc page.
   - Surface live DORA, SLOs, incidents, and experiment status in one portal/dashboard.

8) Refactoring Pipeline (/orchestration/refactor/)
   - Enforce boundaries in a modular-monolith (or service) layout; fail CI on illegal deps.
   - Generate/verify adapters for UIs, DBs, external APIs (ports/adapters).
   - Emit “coupling & cohesion” reports; schedule refactor PRs with safety nets.

9) Branding–Business Interface (/docs/brand/)
   - Keep brand/strategy docs separate but linked; codify Distinctive Assets + Category Entry Points and track where they influence UX content/flows.
   - Ensure no brand artefact can alter functional guards or reliability budgets.

AUTOMATION & CI
- Add GitHub Actions:
  a) decision-lint: ADR present, ACH/pre-mortem attached for medium/high-impact PRs.
  b) delivery-gate: DORA/SLO guardrails; block if regression > thresholds.
  c) experiment-runner: spins up tests (sequential testing), computes CUPED deltas, posts PR comments.
  d) docs-sync: rebuilds Diátaxis docs, verifies links/snippets/diagrams.
  e) AI-eval: ragas suite for any LLM/RAG feature; enforce min grounding scores.
  f) data-contract-check: schema diff + SLAs; break build on incompatible changes.

DELIVERABLES
- New folders + templates as above, plus:
  1) /DECISIONS/ACH_BOARD.md + CLI to create/update matrices.
  2) /RELIABILITY/SLOs.yml with SLIs, SLOs, error budgets, alert policies.
  3) /EXPERIMENTS/playbooks/ with A/B + CUPED + sequential recipes.
  4) /STRATEGY/maps/ initial Wardley maps + render scripts.
  5) /docs/… refreshed, release-ready, with diagrams for flows/process/logic.
  6) Dashboard JSON for Backstage (or plain Grafana) showing DORA, SLOs, experiment velocity, ADR cadence.

SAFETY & PREFLIGHT (must pass before merge)
- All tests + CI jobs green locally and on remote; canary passes; no SLO budget breach.
- AI RMF checklist signed; security scans clean; data contracts valid; diagrams generated; docs build clean.
- Show diffs and produce ORCHESTRATION_REPORT.md summarising debates, decisions, metrics deltas, and follow-ups.

NOTES (implementation references)
- DORA metrics & 2023 findings; golden signals & SLOs; canaries.  [oai_citation:0‡dora.dev](https://dora.dev/research/2023/dora-report/?utm_source=chatgpt.com)
- ADRs + templates; Event Storming; Hexagonal (Ports & Adapters).  [oai_citation:1‡Architectural Decision Records](https://adr.github.io/?utm_source=chatgpt.com)
- Modular monolith rationale & boundaries.  [oai_citation:2‡Thoughtworks](https://www.thoughtworks.com/en-us/insights/blog/microservices/modular-monolith-better-way-build-software?utm_source=chatgpt.com)
- Event-driven patterns & domain events; data contracts.  [oai_citation:3‡martinfowler.com](https://martinfowler.com/articles/201701-event-driven.html?utm_source=chatgpt.com)
- AI agents frameworks (LangGraph, AutoGen, CrewAI) and evals (ragas).  [oai_citation:4‡LangChain AI](https://langchain-ai.github.io/langgraph/?utm_source=chatgpt.com)
- Decision methods: ACH, pre-mortem; Delphi when needed.  [oai_citation:5‡CIA](https://www.cia.gov/resources/csi/static/Tradecraft-Primer-apr09.pdf?utm_source=chatgpt.com)
- Strategy lenses: Wardley, Cynefin, OODA.  [oai_citation:6‡Learn Wardley Mapping](https://learnwardleymapping.com/introduction/?utm_source=chatgpt.com)
- Experiments: sequential testing & CUPED.  [oai_citation:7‡Spotify Engineering](https://engineering.atspotify.com/2023/07/bringing-sequential-testing-to-experiments-with-longitudinal-data-part-1-the-peeking-problem-2-0?utm_source=chatgpt.com)
- AI governance: NIST AI RMF.  [oai_citation:8‡nvlpubs.nist.gov](https://nvlpubs.nist.gov/nistpubs/ai/nist.ai.100-1.pdf?utm_source=chatgpt.com)
