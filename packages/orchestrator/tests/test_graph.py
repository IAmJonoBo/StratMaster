from stratmaster_api.models import WorkflowMetadata
from stratmaster_orchestrator import StrategyState, build_strategy_graph


def test_build_strategy_graph_runs_sequentially_when_langgraph_missing():
    run = build_strategy_graph()
    state = StrategyState(tenant_id="tenant-a", query="brand strategy")
    state.workflow = WorkflowMetadata(workflow_id="wf-1", tenant_id="tenant-a")

    result = run(state)

    assert result.state.decision_brief is not None
    assert result.outcome.decision_brief is not None
    assert "recommender" in result.state.scratchpad
