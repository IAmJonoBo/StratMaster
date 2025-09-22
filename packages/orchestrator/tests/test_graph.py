from stratmaster_api.models import RecommendationStatus, WorkflowMetadata

from stratmaster_orchestrator import StrategyState, build_strategy_graph


def test_strategy_graph_completes_successfully():
    run = build_strategy_graph()
    state = StrategyState(tenant_id="tenant-a", query="growth strategy")
    state.workflow = WorkflowMetadata(workflow_id="wf-1", tenant_id="tenant-a")

    result = run(state)

    assert result.outcome.status is RecommendationStatus.COMPLETE
    assert "cove_verified_fraction" in result.outcome.metrics
    assert result.state.decision_brief is not None
    assert any(turn.role == "ConstitutionalCritic" for turn in result.state.debate.turns)


def test_strategy_graph_marks_failures_when_evals_below_threshold():
    run = build_strategy_graph()
    state = StrategyState(tenant_id="tenant-b", query="red flag scenario")
    state.workflow = WorkflowMetadata(workflow_id="wf-2", tenant_id="tenant-b")

    result = run(state)

    assert result.outcome.status is RecommendationStatus.FAILED
    assert result.outcome.failure_reasons
    assert "factscore" in result.outcome.failure_reasons[0]
