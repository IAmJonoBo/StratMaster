# StratMaster Orchestrator

**Status**: ✅ **COMPLETED** - Production-ready LangGraph orchestration

LangGraph-based orchestration utilities that stitch together the multi-agent workflow
outlined in `PROJECT.md` (Researcher → Synthesiser → Strategist → Adversary →
Constitutional Critic → Recommender).

## ✅ Implemented Modules

- `stratmaster_orchestrator.state` — shared state containers mirroring API data models.
- `stratmaster_orchestrator.agents` — complete agent nodes with MCP-backed implementations.
- `stratmaster_orchestrator.graph` — graph builder returning a LangGraph runnable.
- `stratmaster_orchestrator.tools` — MCP client protocols for research and knowledge services.

## ✅ Production Features

- **Graceful Degradation**: `build_strategy_graph()` degrades gracefully when `langgraph` is not installed, executing nodes sequentially to keep tests lightweight.
- **Agent Integration**: All agent nodes connect to MCP servers, DSPy programs, and evaluation gates.
- **State Management**: Comprehensive state tracking across the multi-agent pipeline.
- **Error Handling**: Robust error handling and recovery mechanisms.

## Usage

```bash
PYTHONPATH=packages/api/src pytest packages/orchestrator/tests -q
```

## Architecture

The orchestrator implements a sophisticated multi-agent debate system with:

1. **Research Agent** - Conducts evidence gathering via research-mcp
2. **Synthesizer** - Combines and analyzes evidence
3. **Strategist** - Develops strategic recommendations
4. **Adversary** - Challenges assumptions and identifies risks
5. **Constitutional Critic** - Ensures compliance and ethics
6. **Recommender** - Final recommendation synthesis

All agents are fully implemented and production-ready.
