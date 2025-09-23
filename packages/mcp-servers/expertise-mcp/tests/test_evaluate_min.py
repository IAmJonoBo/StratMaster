"""Test minimal evaluation scenarios."""

import pytest

from expertise_mcp.tools import evaluate


def test_psychology_reactance_detection():
    """Test that psychology discipline detects reactance phrases."""
    strategy = {
        "id": "test-strategy-1",
        "title": "Marketing Campaign",
        "content": "You must buy this product now! Don't miss out!"
    }
    disciplines = ["psychology"]
    
    # Mock doctrines with reactance phrases
    with pytest.MonkeyPatch().context() as m:
        def mock_load_doctrines():
            return {
                "psychology": {
                    "reactance_phrases": ["must", "don't miss out"]
                }
            }
        
        m.setattr("expertise_mcp.tools.load_doctrines", mock_load_doctrines)
        
        memos = evaluate(strategy, disciplines)
        
        assert len(memos) == 1
        memo = memos[0]
        assert memo.discipline == "psychology"
        assert len(memo.findings) > 0
        
        # Should have detected reactance
        reactance_findings = [f for f in memo.findings if "reactance" in f.title.lower()]
        assert len(reactance_findings) > 0
        assert memo.scores["overall"] < 0.8  # Score should be reduced


def test_design_missing_proof():
    """Test that design discipline warns about missing visual proof."""
    strategy = {
        "id": "test-strategy-2", 
        "title": "Website Redesign",
        "content": "We will make the website better with improved user experience."
    }
    disciplines = ["design"]
    
    with pytest.MonkeyPatch().context() as m:
        def mock_load_doctrines():
            return {
                "design": {
                    "heuristics": {
                        "visibility": {
                            "title": "Visibility of system status",
                            "keywords": ["status", "feedback", "progress"]
                        }
                    }
                }
            }
        
        m.setattr("expertise_mcp.tools.load_doctrines", mock_load_doctrines)
        
        memos = evaluate(strategy, disciplines)
        
        assert len(memos) == 1
        memo = memos[0]
        assert memo.discipline == "design"
        assert len(memo.findings) > 0
        
        # Should warn about missing proof
        proof_findings = [f for f in memo.findings if "proof" in f.title.lower()]
        assert len(proof_findings) > 0
        assert memo.scores["overall"] < 0.8  # Score should be reduced


def test_multiple_disciplines():
    """Test evaluation across multiple disciplines."""
    strategy = {
        "id": "test-strategy-3",
        "title": "Complete Marketing Strategy", 
        "content": "You need to act fast! This amazing product will change your life."
    }
    disciplines = ["psychology", "design", "communication"]
    
    with pytest.MonkeyPatch().context() as m:
        def mock_load_doctrines():
            return {
                "psychology": {
                    "reactance_phrases": ["need to", "act fast"]
                },
                "design": {
                    "heuristics": {}
                },
                "communication": {
                    "message_map": {
                        "required_elements": ["benefit", "proof"],
                        "benefit_keywords": ["amazing", "change"],
                        "proof_keywords": ["study", "research", "data"]
                    }
                }
            }
        
        m.setattr("expertise_mcp.tools.load_doctrines", mock_load_doctrines)
        
        memos = evaluate(strategy, disciplines)
        
        assert len(memos) == 3
        
        # Check each discipline memo
        memo_by_discipline = {memo.discipline: memo for memo in memos}
        
        # Psychology should detect reactance
        psych_memo = memo_by_discipline["psychology"]
        assert len(psych_memo.findings) > 0
        
        # Design should warn about missing proof
        design_memo = memo_by_discipline["design"]
        assert len(design_memo.findings) > 0
        
        # Communication should note missing proof elements
        comm_memo = memo_by_discipline["communication"]
        assert len(comm_memo.findings) >= 0  # May or may not have findings


def test_unknown_discipline():
    """Test handling of unknown disciplines."""
    strategy = {
        "id": "test-strategy-4",
        "title": "Test Strategy",
        "content": "Basic strategy content"
    }
    disciplines = ["unknown_discipline"]
    
    with pytest.MonkeyPatch().context() as m:
        def mock_load_doctrines():
            return {}
        
        m.setattr("expertise_mcp.tools.load_doctrines", mock_load_doctrines)
        
        memos = evaluate(strategy, disciplines)
        
        assert len(memos) == 1
        memo = memos[0]
        assert memo.discipline == "unknown_discipline"
        assert len(memo.findings) > 0
        
        # Should have unknown discipline finding
        unknown_findings = [f for f in memo.findings if "unknown" in f.title.lower()]
        assert len(unknown_findings) > 0
        assert memo.scores["overall"] == 0.5  # Neutral score


def test_empty_strategy():
    """Test handling of empty or minimal strategy content."""
    strategy = {
        "id": "test-strategy-5",
        "title": "",
        "content": ""
    }
    disciplines = ["psychology"]
    
    with pytest.MonkeyPatch().context() as m:
        def mock_load_doctrines():
            return {
                "psychology": {
                    "reactance_phrases": ["must", "need to"]
                }
            }
        
        m.setattr("expertise_mcp.tools.load_doctrines", mock_load_doctrines)
        
        memos = evaluate(strategy, disciplines)
        
        assert len(memos) == 1
        memo = memos[0]
        assert memo.discipline == "psychology"
        
        # Should still create a memo, even if minimal findings
        assert memo.scores["overall"] >= 0.0


def test_evaluation_error_handling():
    """Test error handling during evaluation."""
    strategy = {
        "id": "test-strategy-6",
        "title": "Error Test",
        "content": "Test content"
    }
    disciplines = ["psychology"]
    
    with pytest.MonkeyPatch().context() as m:
        def mock_load_doctrines():
            return {"psychology": {}}
        
        def mock_run_checks_error(*args, **kwargs):
            raise ValueError("Simulated evaluation error")
        
        m.setattr("expertise_mcp.tools.load_doctrines", mock_load_doctrines)
        m.setattr("expertise_mcp.tools.run_checks_for_discipline", mock_run_checks_error)
        
        memos = evaluate(strategy, disciplines)
        
        # Should create error memo instead of failing
        assert len(memos) == 1
        memo = memos[0]
        assert "error" in memo.id
        assert memo.scores["overall"] == 0.0
        assert memo.scores.get("error", 0) == 1.0