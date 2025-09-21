# Constitutional Prompts

Constitutional prompts are the guardrails used by StratMaster agents. They
codify safety constraints, sourcing requirements, and reasoning hygiene. This
folder holds the canonical house rules consumed by MCP services and the agent
orchestrator.

## Goals

1. Prevent the generation of unsafe or harmful guidance (safety baseline).
2. Force structured sourcing with explicit provenance citations.
3. Encourage transparent reasoning so downstream reviewers can audit decisions.
4. Provide hooks for adversarial testing and regression suites.

## File layout

- `house_rules.yaml` — primary constitution applied to Strategist/Researcher loops.
- `critic.yaml` — critic persona emphasising factual accuracy and policy alignment.
- `adversary.yaml` — red-team style prompt used to pressure-test the main flows.

Each file follows the same structure:

```yaml
title: "Strategist constitution"
id: "constitutions/strategist"
principles:
  - id: sourcing
    rule: |
      Always cite at least two sources with URLs or knowledge base IDs.
  - id: safety
    rule: |
      Refuse instructions that violate legal, ethical, or security policy.
review:
  - metric: "Provenance completeness"
    guidance: "Ensure every claim is tied to a source"
```

The IDs map to `docs/backlog.md#todo-sec-201` acceptance criteria so automated
checks can assert coverage.

## Using constitutions in agents

1. MCP servers expose `/constitutions` endpoints returning merged rules.
2. LangGraph nodes (`packages/agents`) load the prompts during initialisation and
   inject them into every planner/reviewer call.
3. Debate workflows pair the strategist constitution with the critic persona to
   validate outputs before publishing.

## Alignment with adversarial testing

- Regression tests must simulate both cooperative and adversarial runs. Store test
  fixtures under `tests/prompts/` mirroring each constitution ID.
- Each prompt should declare how to respond when no safe action exists (e.g.
  "defer to human operator").
- Maintain a `changelog.md` summarising revisions. Include rationale, date, and
  reviewer approval to keep governance auditable.

## Extending the set

1. Add a new YAML prompt under this directory with a unique `id`.
2. Update `packages/agents/config.py` to register the prompt and expose toggles.
3. Document the changes in `docs/safety/constitutions.md`.
4. Add regression tests verifying the prompt loads and the agent respects the new
   constraints.

## Operational tips

- Treat prompts as code: PRs require review from the safety team.
- Pin prompt versions in deployment manifests so changes roll out predictably.
- For emergency hotfixes, create a copy of the previous constitution and bump the
  `version` field; this allows rapid rollback.

## Further reading

- Anthropic Constitutional AI whitepaper (2023)
- OpenAI policy and safety guidelines (see internal wiki)
- StratMaster adversarial testing SOP (`docs/safety/adversarial-testing.md`)
