# Sequential A/B Testing Playbook

1. **Hypothesis Definition**
   - State null and alternative hypotheses explicitly with metric names.
2. **Test Statistic**
   - Use sequential probability ratio test (SPRT) with alpha=0.05, beta=0.2.
   - Minimum sample size gate: 500 exposures per variant before early stopping is permitted.
3. **Monitoring Cadence**
   - Evaluate likelihood ratios hourly; log to `orchestration/experiments/logs/`.
   - Block decisions if guardrail metrics breach thresholds.
4. **Stopping Rules**
   - Stop when LR > (1 - beta) / alpha for acceptance or LR < beta / (1 - alpha) for rejection.
   - Otherwise continue sampling and record status as "in-progress".
5. **Decision Integration**
   - Publish machine-readable result using `strat-orchestrate experiments summarize` (coming soon) so CI can gate releases.
