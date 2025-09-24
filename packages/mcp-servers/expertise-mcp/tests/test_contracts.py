"""Test MCP tool contracts and schemas."""

import json
from unittest.mock import patch


from expertise_mcp.schemas import MEMO_SCHEMA, VOTE_SCHEMA
from expertise_mcp.server import server


def test_memo_schema_is_valid():
    """Test that memo schema is a valid JSON schema."""
    assert isinstance(MEMO_SCHEMA, dict)
    assert "type" in MEMO_SCHEMA
    assert "properties" in MEMO_SCHEMA
    

def test_vote_schema_is_valid():
    """Test that vote schema is a valid JSON schema."""
    assert isinstance(VOTE_SCHEMA, dict)
    assert "type" in VOTE_SCHEMA
    assert "properties" in VOTE_SCHEMA


def test_server_has_required_tools():
    """Test that server has the required tools registered."""
    assert "expert.evaluate" in server.tools
    assert "expert.vote" in server.tools
    
    # Check evaluate tool
    evaluate_tool = server.tools["expert.evaluate"]
    assert "function" in evaluate_tool
    assert "description" in evaluate_tool
    assert "schema" in evaluate_tool
    
    # Check vote tool
    vote_tool = server.tools["expert.vote"]
    assert "function" in vote_tool
    assert "description" in vote_tool
    assert "schema" in vote_tool


def test_tool_schemas_are_valid():
    """Test that tool schemas are valid JSON schemas."""
    for tool_name, tool_info in server.tools.items():
        schema = tool_info["schema"]
        assert isinstance(schema, dict)
        assert "type" in schema
        if "properties" in schema:
            assert isinstance(schema["properties"], dict)


@patch('sys.stdin')
@patch('sys.stdout')
def test_tools_list_request(mock_stdout, mock_stdin):
    """Test handling of tools/list request."""
    # Mock stdin to provide a tools/list request
    mock_stdin.readline.return_value = json.dumps({
        "method": "tools/list",
        "id": 1
    }) + "\n"
    
    # Mock stdout to capture response
    written_data = []
    mock_stdout.write.side_effect = lambda x: written_data.append(x)
    mock_stdout.flush.return_value = None
    
    # This would normally run the server, but we'll test the request handler directly
    request = {"method": "tools/list", "id": 1}
    response = server._handle_request(request)
    
    assert "result" in response
    assert "tools" in response["result"]
    assert len(response["result"]["tools"]) >= 2  # Should have evaluate and vote tools
    
    # Check that each tool has required fields
    for tool in response["result"]["tools"]:
        assert "name" in tool
        assert "description" in tool
        assert "inputSchema" in tool


def test_evaluate_tool_call():
    """Test calling the evaluate tool."""
    request = {
        "method": "tools/call",
        "id": 2,
        "params": {
            "name": "expert.evaluate",
            "arguments": {
                "strategy": {"id": "test-strategy", "content": "Test strategy content"},
                "disciplines": ["psychology"]
            }
        }
    }
    
    with patch('expertise_mcp.tools._eval') as mock_eval:
        # Mock the evaluation function to return a simple memo
        from packages.api.src.stratmaster_api.models.experts.memo import DisciplineMemo
        
        mock_memo = DisciplineMemo(
            id="memo:psychology",
            discipline="psychology",
            applies_to="test-strategy",
            findings=[],
            scores={"overall": 0.8},
            recommendations=[]
        )
        mock_eval.return_value = [mock_memo]
        
        response = server._handle_request(request)
        
        assert "result" in response
        assert "content" in response["result"]
        assert len(response["result"]["content"]) > 0


def test_vote_tool_call():
    """Test calling the vote tool."""
    request = {
        "method": "tools/call",
        "id": 3,
        "params": {
            "name": "expert.vote", 
            "arguments": {
                "strategy_id": "test-strategy",
                "weights": {"psychology": 1.0},
                "memos": [{
                    "id": "memo:psychology",
                    "discipline": "psychology", 
                    "applies_to": "test-strategy",
                    "findings": [],
                    "scores": {"overall": 0.8},
                    "recommendations": []
                }]
            }
        }
    }
    
    with patch('expertise_mcp.tools._vote') as mock_vote:
        # Mock the vote function to return a council vote
        from packages.api.src.stratmaster_api.models.experts.vote import CouncilVote, DisciplineVote
        
        mock_vote_result = CouncilVote(
            id="vote:test-strategy",
            strategy_id="test-strategy",
            votes=[DisciplineVote(id="vote:psychology", discipline="psychology", score=0.8)],
            weighted_score=0.8,
            weights={"psychology": 1.0}
        )
        mock_vote.return_value = mock_vote_result
        
        response = server._handle_request(request)
        
        assert "result" in response
        assert "content" in response["result"]