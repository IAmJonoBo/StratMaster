# StratMaster Orchestrator

LangGraph-based orchestration utilities that stitch together the multi-agent workflow
outlined in `PROJECT.md` (Researcher → Synthesiser → Strategist → Adversary →
Constitutional Critic → Recommender).

## Modules

- `stratmaster_orchestrator.state` — shared state containers mirroring API data models.
- `stratmaster_orchestrator.agents` — placeholder agent nodes; replace with MCP-backed
  implementations.
- `stratmaster_orchestrator.graph` — graph builder returning a LangGraph runnable.

`build_strategy_graph()` degrades gracefully when `langgraph` is not installed, executing
nodes sequentially to keep tests lightweight.

Run package tests with:

```bash
PYTHONPATH=packages/api/src pytest packages/orchestrator/tests -q
```

Future work connects these nodes to MCP servers, DSPy programs, and evaluation gates.
