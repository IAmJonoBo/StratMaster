# Orchestration Kernel Checklists

These checklists encode the operating principles defined in `SCRATCH.md`. They are intended to be consumed by automation and by the orchestration CLI.

## Delivery Performance (DORA-aligned)
- [ ] Capture deploy frequency in `/platform/dashboard/dora_slo_experiments.json`.
- [ ] Record lead time for every epic in `orchestration/planning/planning_backlog.yaml`.
- [ ] Ensure change failure rate < 15% for the rolling 4 week window.
- [ ] Verify mean time to recovery (MTTR) < 60 minutes for Sev2 incidents.
- [ ] Block merges when any metric regresses beyond the guardrail thresholds above.

## Reliability Guardrails
- [ ] Maintain SLIs and SLOs in `RELIABILITY/SLOs.yml` with ownership metadata.
- [ ] Monitor golden signals (latency, traffic, errors, saturation) only.
- [ ] Require canary analysis output saved to `orchestration/refactor/canary_results/` before enabling full rollout.
- [ ] Halt deployment automatically when the active error budget is exhausted.

## Decision Hygiene
- [ ] Every material change references an ADR in `docs/architecture/adr/ADR_INDEX.md`.
- [ ] Run ACH matrix using `strat-orchestrate ach evaluate` with constitutional critique enabled.
- [ ] Execute a pre-mortem using `strat-orchestrate premortem run` for medium/high impact changes.
- [ ] Store machine-readable verdicts in `DECISIONS/ach_results/`.

## Strategy Cadence
- [ ] Maintain Wardley maps in `STRATEGY/maps/` and regenerate mermaid diagrams weekly.
- [ ] Classify initiatives with the Cynefin triage checklist in `orchestration/strategy/cynefin_checklist.md`.
- [ ] Update OODA loop metadata for every roadmap item in `orchestration/strategy/ooda_observe_orient.yaml`.

## AI Governance
- [ ] Apply the NIST AI RMF stages stored in `orchestration/agents/governance_checklist.md`.
- [ ] Require sandbox execution of every AI automation via `orchestration_os.agents.runner.SafeOrchestrator`.
- [ ] Record model evals (ragas, factuality) in `orchestration/experiments/evals/` and gate merges when thresholds fail.

