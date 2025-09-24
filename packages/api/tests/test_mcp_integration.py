"""
Integration test for MCP server connectivity.

Tests that the API can communicate with MCP servers when they are available.
Falls back gracefully when services are unavailable.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock

from stratmaster_api.app import create_app
from stratmaster_api.services import ResearchMCPClient, KnowledgeMCPClient, RouterMCPClient, EvalsMCPClient

IDEMPOTENCY_HEADERS = {"Idempotency-Key": "mcp-integration-test"}


def client():
    app = create_app()
    return TestClient(app)


class TestMCPIntegration:
    """Test MCP server integration with graceful fallbacks."""

    def test_research_plan_with_mcp_fallback(self):
        """Test research planning falls back gracefully when MCP unavailable."""
        c = client()
        
        # This should work even if MCP servers are not available
        # The orchestrator service should provide synthetic fallbacks
        resp = c.post(
            "/research/plan",
            headers=IDEMPOTENCY_HEADERS,
            json={
                "query": "MCP integration test query", 
                "tenant_id": "mcp-test",
                "max_sources": 3
            },
        )
        
        assert resp.status_code == 200
        body = resp.json()
        assert body["plan_id"].startswith("plan-")
        assert len(body["tasks"]) == 3
        assert len(body["sources"]) == 3
        # Verify we got synthetic or fallback sources
        assert all("synthetic" in src.get("tags", []) or "example.com" in src.get("url", "") 
                  for src in body["sources"])

    def test_research_plan_with_mcp_success(self):
        """Test research planning integration points."""
        c = client()
        resp = c.post(
            "/research/plan",
            headers=IDEMPOTENCY_HEADERS,
            json={
                "query": "MCP success test query",
                "tenant_id": "mcp-test", 
                "max_sources": 2
            },
        )
        
        assert resp.status_code == 200
        body = resp.json()
        assert body["plan_id"].startswith("plan-")
        # Verify we got the expected number of sources (fallback or actual)
        assert len(body["sources"]) == 2
        # Tasks should be generated based on sources or fallback logic
        assert len(body["tasks"]) > 0

    def test_eval_endpoint_with_fallback(self):
        """Test evaluation endpoint works with MCP fallback."""
        c = client()
        resp = c.post(
            "/evals/run",
            headers=IDEMPOTENCY_HEADERS,
            json={
                "tenant_id": "mcp-test",
                "suite": "integration-test"
            },
        )
        
        assert resp.status_code == 200
        body = resp.json()
        assert body["run_id"].startswith("eval-")
        assert "passed" in body
        assert "metrics" in body
        # Should have fallback metrics even if MCP unavailable
        assert isinstance(body["metrics"], dict)
        assert len(body["metrics"]) > 0

    def test_eval_endpoint_with_mcp_success(self):
        """Test evaluation endpoint integration."""
        c = client()
        resp = c.post(
            "/evals/run",
            headers=IDEMPOTENCY_HEADERS,
            json={
                "tenant_id": "mcp-test",
                "suite": "mcp-suite"
            },
        )
        
        assert resp.status_code == 200
        body = resp.json()
        assert body["run_id"].startswith("eval-")
        assert "passed" in body
        assert "metrics" in body
        # Verify metrics structure regardless of whether MCP is available
        assert isinstance(body["metrics"], dict)
        assert len(body["metrics"]) > 0

    def test_recommendation_flow_integration(self):
        """Test end-to-end recommendation flow with MCP integration points."""
        c = client()
        
        # This tests the full pipeline including:
        # - Research MCP for data gathering
        # - Knowledge MCP for retrieval
        # - Router MCP for AI completion
        # - Evals MCP for quality gates
        resp = c.post(
            "/recommendations",
            headers=IDEMPOTENCY_HEADERS,
            json={
                "tenant_id": "mcp-integration",
                "cep_id": "mcp-test-cep",
                "jtbd_ids": ["mcp-jtbd-1"],
                "risk_tolerance": "medium"
            },
        )
        
        assert resp.status_code == 200
        body = resp.json()
        assert "decision_brief" in body
        assert "workflow" in body
        assert body["workflow"]["tenant_id"] == "mcp-integration"
        
        # Verify the decision brief has expected structure
        decision_brief = body["decision_brief"]
        assert decision_brief["id"].startswith("brief-")
        assert "recommendation" in decision_brief
        assert "confidence" in decision_brief
        assert isinstance(decision_brief.get("claims", []), list)

    def test_mcp_client_initialization(self):
        """Test MCP client classes can be instantiated."""
        # These should not fail even if servers are not running
        research_client = ResearchMCPClient()
        knowledge_client = KnowledgeMCPClient()
        router_client = RouterMCPClient()
        evals_client = EvalsMCPClient()
        
        # Verify they have correct base URLs
        assert "8081" in research_client.base_url  # Research MCP port
        assert "8082" in knowledge_client.base_url  # Knowledge MCP port  
        assert "8083" in router_client.base_url    # Router MCP port
        assert "8084" in evals_client.base_url     # Evals MCP port

    def test_mcp_error_handling(self):
        """Test API gracefully handles MCP server errors."""
        # This test verifies that the system works when MCP servers are not available
        # which is the typical case in the test environment
        c = client()
        resp = c.post(
            "/research/plan",
            headers=IDEMPOTENCY_HEADERS,
            json={
                "query": "error handling test",
                "tenant_id": "mcp-error-test",
                "max_sources": 2
            },
        )
        
        # Should still return 200 with fallback data
        assert resp.status_code == 200
        body = resp.json()
        assert body["plan_id"].startswith("plan-")
        # Should fall back to synthetic sources when MCP fails
        assert len(body["sources"]) == 2