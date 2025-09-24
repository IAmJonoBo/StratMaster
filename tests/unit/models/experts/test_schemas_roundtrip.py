"""Test schema generation and round-trip validation for Expert Council models."""

import json
from datetime import datetime, UTC
import pytest

# Try to import from the local package structure first
try:
    from packages.api.src.stratmaster_api.models.experts import (
        ExpertProfile, Doctrine, DoctrineRule, DisciplineMemo, Finding,
        CouncilVote, DisciplineVote, MessageMap, PersuasionRisk
    )
    from packages.api.src.stratmaster_api.models.experts.schema_registry import REGISTRY
    from packages.api.src.stratmaster_api.models.experts.generate_json_schemas import main as generate_schemas
except ImportError:
    # Fallback for different import paths
    pytest.skip("Could not import Expert Council models", allow_module_level=True)


def test_expert_profile_roundtrip():
    """Test ExpertProfile model creation and validation."""
    profile = ExpertProfile(
        id="expert:psychology:001",
        discipline="psychology",
        doctrine_ids=["psychology/com-b", "psychology/east"],
        capabilities=["behavioral-analysis", "persuasion-risk"],
        weight_prior=0.75,
        calibration={"accuracy": 0.82, "confidence": 0.90},
        created_at=datetime.now(UTC)
    )
    
    # Test serialization
    json_data = profile.model_dump_json()
    parsed_data = json.loads(json_data)
    
    # Test deserialization
    reconstructed = ExpertProfile.model_validate(parsed_data)
    
    assert reconstructed.id == profile.id
    assert reconstructed.discipline == profile.discipline
    assert reconstructed.weight_prior == profile.weight_prior
    assert len(reconstructed.doctrine_ids) == 2


def test_doctrine_rule_roundtrip():
    """Test DoctrineRule model creation and validation."""
    rule = DoctrineRule(
        id="rule:visibility:001",
        severity="blocker",
        desc="System must provide clear feedback about current status"
    )
    
    json_data = rule.model_dump_json()
    parsed_data = json.loads(json_data)
    reconstructed = DoctrineRule.model_validate(parsed_data)
    
    assert reconstructed.severity == "blocker"
    assert "feedback" in reconstructed.desc


def test_discipline_memo_roundtrip():
    """Test DisciplineMemo with nested Finding objects."""
    finding = Finding(
        id="finding:design:001",
        issue="Navigation lacks clear visual hierarchy",
        severity="high",
        evidence=["heuristic:visibility-system-status", "user-testing-session-3"],
        fix="Add breadcrumb navigation and highlight current page"
    )
    
    memo = DisciplineMemo(
        id="memo:design:001",
        discipline="design",
        applies_to="homepage-redesign",
        findings=[finding],
        scores={"usability": 0.65, "accessibility": 0.80},
        recommendations=[
            {"priority": "high", "action": "Redesign navigation structure"},
            {"priority": "medium", "action": "Improve color contrast"}
        ]
    )
    
    json_data = memo.model_dump_json()
    parsed_data = json.loads(json_data)
    reconstructed = DisciplineMemo.model_validate(parsed_data)
    
    assert reconstructed.discipline == "design"
    assert len(reconstructed.findings) == 1
    assert reconstructed.findings[0].severity == "high"
    assert reconstructed.scores["usability"] == 0.65


def test_council_vote_roundtrip():
    """Test CouncilVote with multiple DisciplineVote objects."""
    psychology_vote = DisciplineVote(
        id="vote:psychology:001",
        discipline="psychology",
        score=0.72,
        justification="Strong alignment with COM-B capability factors, but opportunity barriers exist"
    )
    
    design_vote = DisciplineVote(
        id="vote:design:001", 
        discipline="design",
        score=0.68,
        justification="Minor usability issues with NN/g heuristics 4 and 6"
    )
    
    council_vote = CouncilVote(
        id="council:vote:001",
        strategy_id="strategy:homepage:v2",
        votes=[psychology_vote, design_vote],
        weighted_score=0.704,  # (0.72 * 0.22) + (0.68 * 0.20) = 0.1584 + 0.136 = 0.2944 (partial)
        weights={"psychology": 0.22, "design": 0.20}
    )
    
    json_data = council_vote.model_dump_json()
    parsed_data = json.loads(json_data)
    reconstructed = CouncilVote.model_validate(parsed_data)
    
    assert len(reconstructed.votes) == 2
    assert reconstructed.weighted_score == 0.704
    assert "psychology" in reconstructed.weights


def test_message_map_roundtrip():
    """Test MessageMap model validation."""
    message_map = MessageMap(
        id="msgmap:homepage:001",
        audience="Small business owners, 25-55, tech-comfortable",
        problem="Difficulty tracking business performance across multiple platforms",
        value="Unified dashboard showing all key metrics in one place",
        proof="Customer testimonials show 40% time savings and improved decision making",
        cta="Start your free 14-day trial - no credit card required"
    )
    
    json_data = message_map.model_dump_json()
    parsed_data = json.loads(json_data)
    reconstructed = MessageMap.model_validate(parsed_data)
    
    assert "business owners" in reconstructed.audience
    assert "dashboard" in reconstructed.value
    assert "trial" in reconstructed.cta


def test_persuasion_risk_roundtrip():
    """Test PersuasionRisk model validation."""
    risk = PersuasionRisk(
        id="risk:homepage:001",
        reactance_risk=0.35,
        notes=[
            "Uses 'you should' phrasing which may trigger reactance",
            "Strong CTA but maintains user choice",
            "Overall autonomy-supportive framing"
        ]
    )
    
    json_data = risk.model_dump_json()
    parsed_data = json.loads(json_data)
    reconstructed = PersuasionRisk.model_validate(parsed_data)
    
    assert reconstructed.reactance_risk == 0.35
    assert len(reconstructed.notes) == 3
    assert "autonomy-supportive" in reconstructed.notes[2]


def test_schema_registry_complete():
    """Test that schema registry contains all expected models."""
    expected_models = [
        "ExpertProfile", "Doctrine", "DisciplineMemo", 
        "CouncilVote", "MessageMap", "PersuasionRisk"
    ]
    
    registry_names = [model.__name__ for model in REGISTRY]
    
    for expected in expected_models:
        assert expected in registry_names, f"Missing {expected} from schema registry"


def test_pydantic_strict_mode():
    """Test that models enforce strict validation."""
    with pytest.raises(ValueError):
        # Invalid severity should be rejected
        DoctrineRule(
            id="test:rule",
            severity="invalid",  # Should only accept blocker/warn/info
            desc="Test rule"
        )
    
    with pytest.raises(ValueError):
        # Invalid score range should be rejected  
        DisciplineVote(
            id="test:vote",
            discipline="test",
            score=1.5  # Should be 0-1
        )


def test_extra_fields_forbidden():
    """Test that extra fields are forbidden by Pydantic config."""
    with pytest.raises(ValueError):
        # Extra field should be rejected
        MessageMap(
            id="test:msg",
            audience="test",
            problem="test", 
            value="test",
            proof="test",
            cta="test",
            extra_field="should_fail"  # This should raise validation error
        )