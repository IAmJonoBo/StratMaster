# AI Governance Checklist (NIST AI RMF)

- [ ] Document intended use and context.
- [ ] Assess risks and potential harms; record mitigations.
- [ ] Validate data quality and bias checks.
- [ ] Ensure transparency: log prompts, responses, decisions.
- [ ] Enable human-on-the-loop override for every automated action.
- [ ] Run ragas/factuality evals stored in `orchestration/experiments/evals/`.
- [ ] Approve deployment only when `SafeOrchestrator` marks state as `approved`.
