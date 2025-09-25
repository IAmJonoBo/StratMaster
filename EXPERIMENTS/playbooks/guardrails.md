# Guardrail Metrics Playbook

| Metric | Threshold | Action |
| --- | --- | --- |
| Signup conversion | -2% relative vs control | Pause rollout and run root-cause analysis |
| Crash-free sessions | < 99.5% | Roll back immediately |
| Support ticket volume | +20% vs baseline | Trigger pre-mortem and notify CX lead |
| LLM hallucination rate | > 5% | Block deployment and rerun RAG evals |

Guardrail breaches automatically fail the `delivery-gate` GitHub Action.
