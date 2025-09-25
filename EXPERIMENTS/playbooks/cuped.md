# CUPED Variance Reduction Playbook

1. **Pre-Experiment Checklist**
   - Identify a stable covariate strongly correlated with the outcome metric.
   - Validate covariate availability across control and treatment populations.
2. **Computation**
   - Estimate theta = Cov(Y, X) / Var(X) using pre-experiment data.
   - Adjust outcomes: `Y_adj = Y - theta * (X - mean(X))`.
3. **Reporting**
   - Store theta estimates and diagnostics in `orchestration/experiments/cuped_runs/`.
   - Include uplift, confidence intervals, and guardrail metrics in the final report.
4. **Governance**
   - Document instrumentation changes via ADR and link to the experiment ID.
   - Require review from data science and product analytics leads.
