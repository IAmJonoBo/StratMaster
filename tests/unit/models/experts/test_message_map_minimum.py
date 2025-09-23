"""Test MessageMap minimum requirements and validation."""

import pytest

# Try to import from the local package structure first
try:
    from packages.api.src.stratmaster_api.models.experts import MessageMap
except ImportError:
    pytest.skip("Could not import MessageMap model", allow_module_level=True)


def test_message_map_required_fields():
    """Test that all MessageMap fields are required."""
    # Valid complete MessageMap
    valid_map = MessageMap(
        id="msgmap:test:001",
        audience="Target audience",
        problem="Specific problem statement",
        value="Clear value proposition", 
        proof="Supporting evidence",
        cta="Call to action"
    )
    
    assert valid_map.audience == "Target audience"
    assert valid_map.problem == "Specific problem statement"
    assert valid_map.value == "Clear value proposition"
    assert valid_map.proof == "Supporting evidence"
    assert valid_map.cta == "Call to action"


def test_message_map_missing_fields():
    """Test that missing required fields cause validation errors."""
    
    # Missing audience
    with pytest.raises(ValueError):
        MessageMap(
            id="msgmap:test:001",
            problem="Problem",
            value="Value", 
            proof="Proof",
            cta="CTA"
        )
    
    # Missing problem
    with pytest.raises(ValueError):
        MessageMap(
            id="msgmap:test:001",
            audience="Audience",
            value="Value",
            proof="Proof", 
            cta="CTA"
        )
    
    # Missing value
    with pytest.raises(ValueError):
        MessageMap(
            id="msgmap:test:001",
            audience="Audience",
            problem="Problem",
            proof="Proof",
            cta="CTA"
        )
    
    # Missing proof  
    with pytest.raises(ValueError):
        MessageMap(
            id="msgmap:test:001",
            audience="Audience",
            problem="Problem",
            value="Value",
            cta="CTA"
        )
    
    # Missing cta
    with pytest.raises(ValueError):
        MessageMap(
            id="msgmap:test:001", 
            audience="Audience",
            problem="Problem",
            value="Value",
            proof="Proof"
        )


def test_message_map_empty_strings():
    """Test that empty strings are technically valid but not meaningful."""
    # This should validate but represents poor message quality
    empty_map = MessageMap(
        id="msgmap:test:empty",
        audience="",
        problem="",
        value="", 
        proof="",
        cta=""
    )
    
    # Should validate successfully
    assert empty_map.audience == ""
    assert empty_map.problem == ""
    

def test_message_map_extra_forbidden():
    """Test that extra fields are forbidden by model configuration."""
    with pytest.raises(ValueError, match="extra"):
        MessageMap(
            id="msgmap:test:001",
            audience="Audience", 
            problem="Problem",
            value="Value",
            proof="Proof",
            cta="CTA",
            extra_field="This should fail"
        )


def test_message_map_completeness_check():
    """Test helper function for assessing message map completeness."""
    
    def assess_completeness(message_map: MessageMap) -> float:
        """Calculate completeness score based on content length and quality."""
        scores = []
        
        # Check minimum length requirements
        min_lengths = {
            'audience': 10,  # At least basic demographic info
            'problem': 15,   # Clear problem statement
            'value': 15,     # Meaningful value prop
            'proof': 20,     # Some evidence
            'cta': 10        # Clear action
        }
        
        for field, min_len in min_lengths.items():
            content = getattr(message_map, field)
            if len(content) >= min_len:
                scores.append(1.0)
            else:
                scores.append(len(content) / min_len)
        
        return sum(scores) / len(scores)
    
    # High-quality complete message map
    complete_map = MessageMap(
        id="msgmap:test:complete",
        audience="Small business owners, 25-45, revenue $100K-$500K, currently using spreadsheets",
        problem="Spending 5+ hours weekly on manual financial reporting and struggling to identify trends",
        value="Automated reporting dashboard that provides real-time insights and saves 80% of reporting time",
        proof="Beta customers report average 4.2 hour weekly savings and 23% faster decision making",
        cta="Start your free 30-day trial today - setup takes less than 10 minutes"
    )
    
    # Minimal message map
    minimal_map = MessageMap(
        id="msgmap:test:minimal", 
        audience="Businesses",
        problem="Reports",
        value="Dashboard",
        proof="Works well",
        cta="Try it"
    )
    
    complete_score = assess_completeness(complete_map)
    minimal_score = assess_completeness(minimal_map)
    
    assert complete_score == 1.0  # Should score perfectly
    assert minimal_score < 0.85   # Should score below threshold
    assert complete_score > minimal_score


def test_message_map_id_pattern():
    """Test that ID follows expected pattern from base model."""
    
    # Valid ID patterns
    valid_ids = [
        "msgmap:homepage:001",
        "message-map:campaign:v2", 
        "msgmap:a-b-test:variant-1",
        "communication:map:2024.q1"
    ]
    
    for valid_id in valid_ids:
        map_obj = MessageMap(
            id=valid_id,
            audience="Test audience",
            problem="Test problem", 
            value="Test value",
            proof="Test proof",
            cta="Test CTA"
        )
        assert map_obj.id == valid_id
    
    # Invalid ID patterns (should fail regex validation)
    invalid_ids = [
        "Invalid ID with spaces",
        "UPPERCASE_NOT_ALLOWED",
        "special!@#$%characters"
    ]
    
    for invalid_id in invalid_ids:
        with pytest.raises(ValueError):
            MessageMap(
                id=invalid_id,
                audience="Test",
                problem="Test",
                value="Test", 
                proof="Test",
                cta="Test"
            )