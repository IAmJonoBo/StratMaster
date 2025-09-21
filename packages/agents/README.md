# Agents Package

This package defines StratMaster's LangGraph agent network, shared state schema,
and orchestration utilities.

## Architecture

- **Researcher** — gathers evidence via MCP connectors (Knowledge, Research, SearxNG).
- **Synthesiser** — aggregates evidence, runs debate loops, and drafts recommendations.
- **Strategist** — validates outputs against constitutions, orchestrates follow-up actions.
- **Critic/Adversary** — optional nodes used for constitutional evaluation.

Agents communicate through a shared `AgentState` object defined in
`packages/agents/src/agents/state.py`.

### Shared state schema

```python
class AgentState(BaseModel):
    tenant_id: str
    task_id: str
    hypotheses: list[Hypothesis]
    evidence: list[Evidence]
    plan: Plan | None
    debate_log: list[DebateTurn]
    status: Literal["pending", "in_progress", "needs_review", "complete", "failed"]
```

- `Hypothesis` objects include provenance, fingerprints, and confidence.
- `Evidence` tracks MCP call outputs with citations.
- LangGraph nodes mutate state immutably (return new copies) to simplify auditing.

## Tool mediation

- Tool registry lives in `packages/agents/src/agents/tools.py` and exposes
  connectors with capability metadata (rate limits, allowed tenants).
- Tools implement a common protocol returning `ToolResult` with `success`,
  `data`, and `provenance` fields.
- Planner nodes choose tools based on `models-policy` task routing.

## LangGraph wiring

```
Researcher → Synthesiser ↘
             ↑          Strategist → Output
Adversary ----↗
```

- Graph defined in `graph.py`; edges capture transitions based on state flags.
- Checkpointing is enabled via `AgentStateCheckpointStore` which persists JSON
  snapshots to Postgres (`stratmaster_agents.checkpoints`).
- Resume semantics: load latest checkpoint by `task_id`, replay pending actions.

## Debate & constitutional checks

- Synthesiser spawns a debate between strategist and adversary prompts when
  `state.requires_debate` is true (e.g. low confidence or conflicting evidence).
- Debate transcripts stored in `debate_log`; critic node evaluates transcripts
  using constitutional prompts from `prompts/constitutions`.
- If the critic rejects the output, the graph re-enters research mode with
  actionable feedback.

## Temporal integration

- Temporal workflow `agents.execute_task` wraps LangGraph execution.
- Workflow checkpoints state after each node via `checkpoint_state` activity.
- Failures trigger retries with exponential backoff; after 3 attempts the workflow
  emits a `needs_review` status and notifies operators.

## Testing

- Unit tests under `packages/agents/tests` cover state transitions and tool stubs.
- `make test.agents` runs the suite including deterministic LangGraph simulations.
- Snapshot tests assert the JSON schema exported by `AgentState` remains stable.

## Extending the graph

1. Add a new node under `src/agents/nodes/<name>.py` implementing `LangGraphNode`.
2. Register the node in `graph.py` with transitions and guard conditions.
3. Update `state.py` if additional fields are required.
4. Document new capabilities in `docs/agents/architecture.md` and add regression
   tests verifying behaviour.

## Observability

- LangGraph emits OTEL traces; spans tagged with `agent.node` and `tenant_id`.
- Langfuse integration records prompt/response pairs per node for later review.
- Metrics exported via Prometheus: tasks completed, average debate rounds, retry counts.
