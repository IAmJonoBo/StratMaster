# Debate Engine

The debate engine provides repeatable workflows for Analysis of Competing Hypotheses (ACH) and pre-mortem sessions. It also performs constitutional critique and self-consistency checks before a recommendation is allowed to progress into implementation.

Use the CLI exposed via `strat-orchestrate`:

```bash
# Generate a template ACH matrix
strat-orchestrate ach init-template --path DECISIONS/ach_inputs/sample_ach.json

# Evaluate a populated template and emit JSON + board updates
strat-orchestrate ach evaluate --input DECISIONS/ach_inputs/sample_ach.json \
  --output DECISIONS/ach_results/sample_ach.json \
  --board DECISIONS/ACH_BOARD.md

# Run a pre-mortem
strat-orchestrate premortem run --input DECISIONS/premortems/feature_launch.json \
  --output DECISIONS/premortems/feature_launch_report.md

# Or run the full decision-support bundle with orchestration integration
strat-orchestrate bundle --query "Should we launch the adaptive insights feature?" \
  --ach-input DECISIONS/ach_inputs/sample_ach.json \
  --premortem-input DECISIONS/premortems/feature_launch.json
```

Outputs are designed to be machine-readable so CI/CD pipelines can block deployments when a hypothesis is rejected or when critique issues remain unresolved.
