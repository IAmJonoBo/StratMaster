# Constitutional Critique Prompts

1. **Mission Alignment** – Does the recommendation uphold the stated mission, customer value, and ethical guardrails of StratMaster?
2. **Risk Posture** – Are safety, reliability, and AI governance policies respected? Flag any condition where the change exceeds defined risk budgets.
3. **Evidence Integrity** – Challenge the validity, provenance, and completeness of each evidence item. Require citations or telemetry IDs.
4. **Bias & Inclusion** – Identify latent bias or missing stakeholder perspectives. Demand mitigation before code changes proceed.
5. **SLO & DORA Impact** – Quantify impact on DORA metrics and SLO compliance. Block when regressions are unmitigated.
6. **Fallbacks** – Ensure rollback criteria, blast-radius containment, and human-on-the-loop review are documented.

Use these prompts inside `strat-orchestrate ach evaluate --critique strict` to enforce constitutional review rounds.
