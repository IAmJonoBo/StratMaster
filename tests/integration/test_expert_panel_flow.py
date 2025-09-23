"""Integration test for expert panel evaluation flow."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from stratmaster_api.app import create_app


@pytest.fixture
def client():
    """Create test client."""
    app = create_app()
    return TestClient(app)


@pytest.fixture
def mock_mcp_client():
    """Mock MCP client for expertise server."""
    client = MagicMock()
    return client


class TestExpertPanelFlow:
    """Test the complete expert panel evaluation flow."""
    
    def test_evaluate_endpoint_success(self, client, mock_mcp_client):
        """Test successful evaluation via API endpoint."""
        # Mock MCP client response
        mock_mcp_response = [{
            "id": "memo:psychology",
            "discipline": "psychology",
            "applies_to": "test-strategy",
            "findings": [{
                "id": "psych_reactance",
                "severity": "warning",
                "title": "Psychological reactance detected",
                "description": "Found potentially triggering phrases"
            }],
            "scores": {"overall": 0.5},
            "recommendations": ["Consider rewording to reduce psychological reactance"]
        }]
        
        mock_mcp_client.call.return_value = mock_mcp_response
        
        # Patch the MCP client dependency
        with patch('stratmaster_api.routers.experts.get_mcp_client', return_value=mock_mcp_client):
            response = client.post(
                "/experts/evaluate",
                json={
                    "strategy": {
                        "id": "test-strategy",
                        "title": "Test Campaign", 
                        "content": "You must buy this now!"
                    },
                    "disciplines": ["psychology"]
                }
            )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["discipline"] == "psychology"
        assert len(data[0]["findings"]) == 1
        assert data[0]["scores"]["overall"] == 0.5
    
    def test_vote_endpoint_success(self, client, mock_mcp_client):
        """Test successful vote aggregation via API endpoint."""
        # Mock MCP client response
        mock_mcp_response = {
            "id": "vote:test-strategy",
            "strategy_id": "test-strategy",
            "votes": [{
                "id": "vote:psychology",
                "discipline": "psychology",
                "score": 0.5
            }],
            "weighted_score": 0.5,
            "weights": {"psychology": 1.0}
        }
        
        mock_mcp_client.call.return_value = mock_mcp_response
        
        # Patch the MCP client dependency  
        with patch('stratmaster_api.routers.experts.get_mcp_client', return_value=mock_mcp_client):
            response = client.post(
                "/experts/vote",
                json={
                    "strategy_id": "test-strategy",
                    "weights": {"psychology": 1.0},
                    "memos": [{
                        "id": "memo:psychology",
                        "discipline": "psychology",
                        "applies_to": "test-strategy", 
                        "findings": [],
                        "scores": {"overall": 0.5},
                        "recommendations": []
                    }]
                }
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["strategy_id"] == "test-strategy"
        assert data["weighted_score"] == 0.5
        assert len(data["votes"]) == 1
    
    def test_health_endpoint(self, client):
        """Test health check endpoint."""
        response = client.get("/experts/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "experts"
    
    def test_evaluate_validation_error(self, client):
        """Test validation error on invalid input."""
        response = client.post(
            "/experts/evaluate",
            json={
                "strategy": "invalid",  # Should be object
                "disciplines": "invalid"  # Should be array
            }
        )
        assert response.status_code == 422  # Validation error
    
    def test_vote_validation_error(self, client):
        """Test validation error on vote endpoint."""
        response = client.post(
            "/experts/vote",
            json={
                "strategy_id": 123,  # Should be string
                "weights": "invalid",  # Should be object
                "memos": "invalid"  # Should be array
            }
        )
        assert response.status_code == 422  # Validation error
    
    def test_mcp_client_error(self, client, mock_mcp_client):
        """Test handling of MCP client errors."""
        mock_mcp_client.call.side_effect = Exception("MCP connection failed")
        
        with patch('stratmaster_api.routers.experts.get_mcp_client', return_value=mock_mcp_client):
            response = client.post(
                "/experts/evaluate",
                json={
                    "strategy": {"id": "test", "content": "test"},
                    "disciplines": ["psychology"]
                }
            )
        
        assert response.status_code == 500
        assert "Evaluation failed" in response.json()["detail"]
    
    def test_full_evaluation_flow(self, client, mock_mcp_client):
        """Test complete evaluation and voting flow."""
        # Mock evaluation response
        eval_response = [{
            "id": "memo:psychology",
            "discipline": "psychology", 
            "applies_to": "strategy-1",
            "findings": [{
                "id": "finding-1",
                "severity": "info",
                "title": "Test finding",
                "description": "Test description"
            }],
            "scores": {"overall": 0.8},
            "recommendations": ["Test recommendation"]
        }, {
            "id": "memo:design",
            "discipline": "design",
            "applies_to": "strategy-1", 
            "findings": [],
            "scores": {"overall": 0.6},
            "recommendations": ["Add visual proof"]
        }]
        
        # Mock vote response
        vote_response = {
            "id": "vote:strategy-1",
            "strategy_id": "strategy-1",
            "votes": [
                {"id": "vote:psychology", "discipline": "psychology", "score": 0.8},
                {"id": "vote:design", "discipline": "design", "score": 0.6}
            ],
            "weighted_score": 0.7,
            "weights": {"psychology": 0.5, "design": 0.5}
        }
        
        mock_mcp_client.call.side_effect = [eval_response, vote_response]
        
        with patch('stratmaster_api.routers.experts.get_mcp_client', return_value=mock_mcp_client):
            # Step 1: Evaluate
            eval_response = client.post(
                "/experts/evaluate", 
                json={
                    "strategy": {
                        "id": "strategy-1",
                        "title": "Marketing Campaign",
                        "content": "Great product for everyone!"
                    },
                    "disciplines": ["psychology", "design"]
                }
            )
            
            assert eval_response.status_code == 200
            memos = eval_response.json()
            assert len(memos) == 2
            
            # Step 2: Vote
            vote_response = client.post(
                "/experts/vote",
                json={
                    "strategy_id": "strategy-1",
                    "weights": {"psychology": 0.5, "design": 0.5},
                    "memos": memos
                }
            )
            
            assert vote_response.status_code == 200
            vote_data = vote_response.json()
            assert vote_data["weighted_score"] == 0.7
            assert len(vote_data["votes"]) == 2
    
    def test_empty_disciplines_list(self, client, mock_mcp_client):
        """Test evaluation with empty disciplines list."""
        mock_mcp_client.call.return_value = []
        
        with patch('stratmaster_api.routers.experts.get_mcp_client', return_value=mock_mcp_client):
            response = client.post(
                "/experts/evaluate",
                json={
                    "strategy": {"id": "test", "content": "test"},
                    "disciplines": []
                }
            )
        
        assert response.status_code == 200
        assert response.json() == []
    
    def test_default_disciplines(self, client, mock_mcp_client):
        """Test that default disciplines are used when not specified."""
        mock_mcp_client.call.return_value = []
        
        with patch('stratmaster_api.routers.experts.get_mcp_client', return_value=mock_mcp_client):
            response = client.post(
                "/experts/evaluate",
                json={
                    "strategy": {"id": "test", "content": "test"}
                    # disciplines not specified - should use defaults
                }
            )
        
        assert response.status_code == 200
        
        # Verify MCP was called with default disciplines
        mock_mcp_client.call.assert_called_once()
        call_args = mock_mcp_client.call.call_args[0][1]
        expected_disciplines = ["psychology", "design", "communication", "brand_science", "economics"]
        assert call_args["disciplines"] == expected_disciplines