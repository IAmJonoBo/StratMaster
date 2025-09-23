"""Integration tests for enhanced DSPy telemetry and debate system."""

from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from stratmaster_dsp import (
    TelemetryRecorder,
    compile_full_pipeline,
    compile_research_planner,
    compile_strategy_planner,
    compile_synthesis_planner,
)


def test_enhanced_telemetry_recorder():
    """Test enhanced telemetry recorder with local fallback."""
    recorder = TelemetryRecorder()
    
    # Test basic recording
    recorder.record("test_event", {"key": "value"})
    assert len(recorder.events) == 1
    assert recorder.events[0]["event_type"] == "test_event"
    assert recorder.events[0]["key"] == "value"
    assert "timestamp" in recorder.events[0]

    # Test trace functionality (should work with or without Langfuse)
    trace_id = recorder.start_trace("test_trace", metadata="test")
    assert len(recorder.events) == 2
    assert recorder.events[1]["event_type"] == "trace.start"
    
    recorder.record_generation("test_gen", {"input": "test"}, {"output": "result"})
    assert len(recorder.events) == 3
    assert recorder.events[2]["event_type"] == "generation"
    
    recorder.record_score("test_score", 0.85)
    assert len(recorder.events) == 4
    assert recorder.events[3]["event_type"] == "score"
    assert recorder.events[3]["value"] == 0.85
    
    recorder.end_trace(success=True)
    assert len(recorder.events) == 5
    assert recorder.events[4]["event_type"] == "trace.end"


def test_enhanced_research_planner():
    """Test enhanced research planner with telemetry integration."""
    with TemporaryDirectory() as tmp_dir:
        telemetry = TelemetryRecorder()
        
        artifact_path = compile_research_planner(
            "AI-powered customer insights",
            output_dir=Path(tmp_dir),
            telemetry=telemetry
        )
        
        assert artifact_path.exists()
        
        # Check telemetry events
        compile_events = [e for e in telemetry.events if e["event_type"] == "dspy.compile"]
        assert len(compile_events) == 1
        assert compile_events[0]["program"] == "research_planner"
        
        # Check trace events
        trace_events = [e for e in telemetry.events if e["event_type"].startswith("trace.")]
        assert len(trace_events) >= 2  # start and end
        
        # Check generation events
        gen_events = [e for e in telemetry.events if e["event_type"] == "generation"]
        assert len(gen_events) >= 1
        
        # Check artifact content
        import json
        artifact_data = json.loads(artifact_path.read_text())
        assert "compilation_metrics" in artifact_data
        assert artifact_data["compilation_metrics"]["step_count"] == 5  # Enhanced from 3 to 5 steps


def test_synthesis_planner():
    """Test new synthesis planner."""
    with TemporaryDirectory() as tmp_dir:
        telemetry = TelemetryRecorder()
        research_findings = [
            "Market demand shows 35% growth",
            "Competitor analysis reveals gaps", 
            "Regulatory requirements are manageable"
        ]
        
        artifact_path = compile_synthesis_planner(
            research_findings,
            output_dir=Path(tmp_dir),
            telemetry=telemetry
        )
        
        assert artifact_path.exists()
        
        # Check artifact
        import json
        artifact_data = json.loads(artifact_path.read_text())
        assert artifact_data["program_name"] == "synthesis_planner"
        assert len(artifact_data["steps"]) >= len(research_findings)  # Should generate insights
        assert "compilation_metrics" in artifact_data
        assert artifact_data["compilation_metrics"]["synthesis_ratio"] > 0


def test_strategy_planner():
    """Test new strategy planner."""
    with TemporaryDirectory() as tmp_dir:
        telemetry = TelemetryRecorder()
        insights = [
            "Strategic insight 1: Market opportunity identified",
            "Strategic insight 2: Competitive advantage available"
        ]
        
        artifact_path = compile_strategy_planner(
            insights,
            output_dir=Path(tmp_dir),
            telemetry=telemetry
        )
        
        assert artifact_path.exists()
        
        # Check artifact
        import json
        artifact_data = json.loads(artifact_path.read_text())
        assert artifact_data["program_name"] == "strategy_planner"
        assert len(artifact_data["steps"]) >= len(insights) + 3  # Insights + meta-recommendations
        assert "compilation_metrics" in artifact_data


def test_full_pipeline_compilation():
    """Test full DSPy pipeline compilation."""
    with TemporaryDirectory() as tmp_dir:
        telemetry = TelemetryRecorder()
        
        result = compile_full_pipeline(
            "international market expansion",
            output_dir=Path(tmp_dir),
            telemetry=telemetry
        )
        
        # Check all three components were created
        assert "research" in result
        assert "synthesis" in result  
        assert "strategy" in result
        
        assert result["research"].exists()
        assert result["synthesis"].exists()
        assert result["strategy"].exists()
        
        # Check telemetry recorded pipeline events
        pipeline_events = [e for e in telemetry.events if e["event_type"] == "trace.start" and "pipeline" in e.get("name", "")]
        assert len(pipeline_events) >= 1


def test_constitutional_compliance_validation():
    """Test that the enhanced system validates constitutional compliance."""
    # This would test the enhanced ConstitutionalCritic
    # For now, we verify the structure is in place
    
    try:
        from stratmaster_orchestrator.agents import ConstitutionalCriticNode
        from stratmaster_orchestrator.prompts import load_prompts
        from stratmaster_orchestrator.tools import EvaluationGate
        
        # This confirms the enhanced critic can be imported
        prompts = load_prompts()
        assert "house" in prompts.house
        assert "principles" in prompts.critic
        
        # Verify enhanced evaluation gate
        gate = EvaluationGate({
            "constitutional_compliance": 1.0,
            "verification_confidence": 0.7
        })
        
        # Test the gate logic
        passed, failures = gate.check({
            "constitutional_compliance": 1.0,
            "verification_confidence": 0.8
        })
        assert passed
        assert len(failures) == 0
        
        passed, failures = gate.check({
            "constitutional_compliance": 0.5,
            "verification_confidence": 0.8
        })
        assert not passed
        assert len(failures) == 1
        
    except ImportError as e:
        pytest.skip(f"Orchestrator components not available: {e}")


def test_chain_of_verification_structure():
    """Test Chain-of-Verification structure."""
    try:
        from stratmaster_orchestrator.verification import (
            ChainOfVerificationNode,
            VerificationQuestion,
            VerificationAnswer,
            VerificationResult
        )
        
        # Test data structures
        question = VerificationQuestion(
            id="test-1",
            question="Is this claim valid?",
            claim_id="claim-1", 
            verification_type="factual"
        )
        
        assert question.id == "test-1"
        assert question.verification_type == "factual"
        
        answer = VerificationAnswer(
            question_id="test-1",
            answer="Yes, the claim is valid",
            confidence=0.8,
            supporting_evidence=["source-1"],
            conflicts_detected=False
        )
        
        assert answer.confidence == 0.8
        assert not answer.conflicts_detected
        
        result = VerificationResult(
            questions=[question],
            answers=[answer],
            verified_claims=["claim-1"],
            flagged_claims=[],
            amendments=[],
            overall_confidence=0.8
        )
        
        assert result.overall_confidence == 0.8
        assert len(result.verified_claims) == 1
        
    except ImportError as e:
        pytest.skip(f"Verification components not available: {e}")


if __name__ == "__main__":
    pytest.main([__file__])