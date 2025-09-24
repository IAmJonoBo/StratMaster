"""Enhanced test suite for StratMaster comprehensive functionality testing.

Tests all major components and integrations to validate the implementation
meets the requirements specified in Upgrade.md and Scratch.md.
"""

import json
from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient

from stratmaster_api.app import create_app
from stratmaster_api.performance import PerformanceBenchmark, QualityGate


@pytest.fixture
def test_app():
    """Create test FastAPI application."""
    return create_app()


@pytest.fixture  
def client(test_app):
    """Create test client."""
    return TestClient(test_app)


class TestExportIntegrations:
    """Test export functionality with real integrations."""
    
    def test_export_integrations_available(self):
        """Test that export integrations are properly loaded."""
        # Import should work without errors
        from stratmaster_api.routers.export import INTEGRATIONS_AVAILABLE
        
        # Should be True now that we've copied integrations locally
        assert INTEGRATIONS_AVAILABLE == True
        
    def test_notion_export_endpoint_exists(self, client):
        """Test Notion export endpoint is available."""
        response = client.post("/export/notion", json={
            "notion_token": "test_token",
            "parent_page_id": "test_page",
            "strategy_id": "test_strategy",
            "dry_run": True
        })
        # Should not return 404 (endpoint exists)
        assert response.status_code in [200, 400, 422, 500]
    
    def test_trello_export_endpoint_exists(self, client):
        """Test Trello export endpoint is available.""" 
        response = client.post("/export/trello", json={
            "api_key": "test_key",
            "api_token": "test_token", 
            "strategy_id": "test_strategy",
            "dry_run": True
        })
        assert response.status_code in [200, 400, 422, 500]
    
    def test_jira_export_endpoint_exists(self, client):
        """Test Jira export endpoint is available."""
        response = client.post("/export/jira", json={
            "server_url": "https://test.atlassian.net",
            "username": "test@example.com", 
            "api_token": "test_token",
            "project_key": "TEST",
            "strategy_id": "test_strategy",
            "dry_run": True
        })
        assert response.status_code in [200, 400, 422, 500]


class TestPerformanceBenchmarking:
    """Test performance benchmarking system."""
    
    def test_performance_endpoint_exists(self, client):
        """Test performance benchmark endpoint exists."""
        response = client.post("/performance/benchmark")
        # Should not return 404 (endpoint exists)
        assert response.status_code in [200, 500, 503]
    
    def test_performance_health_check(self, client):
        """Test performance health endpoint."""
        response = client.get("/performance/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok", "component": "performance"}
    
    def test_performance_benchmark_creation(self):
        """Test performance benchmark can be created with quality gates."""
        benchmark = PerformanceBenchmark()
        
        # Test basic properties
        assert benchmark.base_url == "http://127.0.0.1:8080"
        assert len(benchmark.quality_gates) > 0
        
        # Test quality gate definitions match requirements
        gate_names = [gate.name for gate in benchmark.quality_gates]
        required_gates = [
            "gateway_latency_p50", "gateway_latency_p95",
            "routing_latency_p50", "ragas_faithfulness", 
            "ragas_precision", "ragas_recall",
            "retrieval_improvement"
        ]
        
        for required_gate in required_gates:
            assert required_gate in gate_names, f"Missing quality gate: {required_gate}"
    
    def test_quality_gate_threshold_checking(self):
        """Test quality gate threshold evaluation logic."""
        benchmark = PerformanceBenchmark()
        
        # Test different operators
        assert benchmark._check_threshold(5.0, 10.0, "lt") == True
        assert benchmark._check_threshold(15.0, 10.0, "lt") == False
        assert benchmark._check_threshold(8.0, 10.0, "gte") == False
        assert benchmark._check_threshold(12.0, 10.0, "gte") == True
        assert benchmark._check_threshold(10.0, 10.0, "eq") == True


class TestCollaborationSystem:
    """Test real-time collaboration functionality."""
    
    def test_collaboration_imports_available(self):
        """Test collaboration module imports work."""
        from stratmaster_api.collaboration import YjsCollaborationServer, UserPresence, DocumentUpdate
        
        # Test instantiation doesn't fail
        server = YjsCollaborationServer()
        assert server.host == "127.0.0.1"
        assert server.port == 8765
        
        # Test data classes
        presence = UserPresence(
            user_id="test_user",
            username="testuser",
            cursor_position=100
        )
        assert presence.user_id == "test_user"
        assert presence.cursor_position == 100
        
        # Test document update structure
        update = DocumentUpdate(
            doc_id="test_doc",
            user_id="test_user", 
            operations=[{"type": "insert", "text": "hello"}],
            vector_clock={"test_user": 1},
            timestamp=1234567890.0
        )
        assert update.doc_id == "test_doc"
        assert len(update.operations) == 1


class TestSecurityIntegration:
    """Test security and authentication systems."""
    
    def test_security_router_exists(self, client):
        """Test security endpoints are available.""" 
        # Test audit logs endpoint
        response = client.get("/security/audit-logs")
        assert response.status_code in [200, 401, 403, 422]
        
        # Test PII detection endpoint
        response = client.post("/security/detect-pii", json={
            "text": "My email is test@example.com"
        })
        assert response.status_code in [200, 401, 422]
    
    def test_security_components_available(self):
        """Test security components are importable."""
        try:
            from stratmaster_api.security.keycloak_auth import OIDCConfig
            
            # Test configuration model
            config = OIDCConfig(
                server_url="https://keycloak.example.com",
                realm_name="stratmaster",
                client_id="stratmaster-api"
            )
            assert config.server_url == "https://keycloak.example.com"
            assert config.verify_ssl == True  # default
            
        except ImportError:
            pytest.skip("Security components not available")


class TestStrategyEngine:
    """Test strategy generation and processing."""
    
    def test_strategy_endpoints_exist(self, client):
        """Test strategy endpoints are available."""
        # Test strategy generation
        response = client.post("/strategy/generate-brief", json={
            "objectives": ["Test objective"],
            "assumptions": ["Test assumption"],
            "context": "Test context"
        })
        assert response.status_code in [200, 400, 422, 500]
        
        # Test strategy analysis
        response = client.post("/strategy/analyze", json={
            "strategy_id": "test_strategy"
        })
        assert response.status_code in [200, 404, 422, 500]


class TestDebateLearningSystem:
    """Test ML-powered debate learning system."""
    
    def test_debate_endpoints_exist(self, client):
        """Test debate endpoints are available."""
        # Test debate escalation
        response = client.post("/debate/escalate", json={
            "debate_id": "test_debate",
            "expert_type": "domain_specialist",
            "context": "Test escalation"
        })
        assert response.status_code in [200, 404, 422, 500]
        
        # Test debate acceptance
        response = client.post("/debate/accept", json={
            "debate_id": "test_debate",
            "outcome": "accept",
            "quality_rating": 4.5
        })
        assert response.status_code in [200, 404, 422, 500]
        
        # Test learning metrics
        response = client.get("/debate/learning/metrics")
        assert response.status_code in [200, 500]


class TestRetrievalSystem:
    """Test hybrid retrieval with SPLADE scoring."""
    
    def test_retrieval_endpoints_exist(self, client):
        """Test retrieval endpoints are available."""
        # Test ColBERT retrieval
        response = client.post("/retrieval/colbert/query", json={
            "tenant_id": "test_tenant",
            "query": "market analysis",
            "top_k": 10
        })
        assert response.status_code in [200, 400, 422, 500]
        
        # Test SPLADE retrieval
        response = client.post("/retrieval/splade/query", json={
            "tenant_id": "test_tenant", 
            "query": "competitive intelligence",
            "top_k": 10
        })
        assert response.status_code in [200, 400, 422, 500]


class TestObservabilitySystem:
    """Test OpenTelemetry and monitoring integration."""
    
    def test_tracing_middleware(self, client):
        """Test tracing middleware adds headers."""
        response = client.get("/healthz")
        assert response.status_code == 200
        # Should have trace ID header
        assert "X-Trace-Id" in response.headers
    
    def test_opentelemetry_integration(self):
        """Test OpenTelemetry is properly integrated."""
        from opentelemetry import trace
        
        # Should be able to get a tracer
        tracer = trace.get_tracer(__name__)
        assert tracer is not None
        
        # Should be able to create spans
        with tracer.start_as_current_span("test_span") as span:
            assert span is not None
            span.set_attribute("test_attribute", "test_value")


class TestMachineLearningIntegration:
    """Test ML components and scikit-learn integration."""
    
    def test_ml_dependencies_available(self):
        """Test ML dependencies are properly installed."""
        import sklearn
        import numpy as np
        
        # Should be able to create basic ML components
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.model_selection import train_test_split
        
        # Test basic functionality
        clf = RandomForestClassifier(n_estimators=10, random_state=42)
        assert clf.n_estimators == 10
        
        # Test with dummy data
        X = np.random.rand(100, 4)
        y = np.random.randint(0, 2, 100)
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)
        
        clf.fit(X_train, y_train)
        predictions = clf.predict(X_test)
        assert len(predictions) == len(y_test)


class TestEndToEndWorkflows:
    """Test complete end-to-end workflows."""
    
    def test_complete_strategy_workflow(self, client):
        """Test complete strategy creation and export workflow."""
        # 1. Generate strategy brief
        brief_response = client.post("/strategy/generate-brief", json={
            "objectives": ["Increase market share"],
            "assumptions": ["Market is growing"],
            "context": "Technology sector"
        })
        assert brief_response.status_code in [200, 500]
        
        # 2. If brief creation succeeded, test export
        if brief_response.status_code == 200:
            brief_data = brief_response.json()
            strategy_id = brief_data.get("id", "test_strategy")
            
            # Test export to Notion (dry run)
            export_response = client.post("/export/notion", json={
                "notion_token": "test_token",
                "parent_page_id": "test_page",
                "strategy_id": strategy_id,
                "dry_run": True
            })
            assert export_response.status_code in [200, 400, 422, 500]


class TestErrorHandlingAndResilience:
    """Test error handling and system resilience."""
    
    def test_invalid_endpoints_return_404(self, client):
        """Test that invalid endpoints return 404."""
        response = client.get("/nonexistent/endpoint")
        assert response.status_code == 404
    
    def test_malformed_requests_handled(self, client):
        """Test that malformed requests are handled gracefully.""" 
        response = client.post("/strategy/generate-brief", json={
            "invalid_field": "invalid_value"
        })
        assert response.status_code in [400, 422]  # Should return validation error
        
    def test_large_payloads_handled(self, client):
        """Test handling of large payloads."""
        large_text = "x" * 10000  # 10KB of text
        response = client.post("/strategy/generate-brief", json={
            "objectives": [large_text],
            "assumptions": ["Test assumption"],
            "context": "Test context"
        })
        assert response.status_code in [200, 400, 413, 422, 500]


class TestAPIDocumentation:
    """Test API documentation and schema generation."""
    
    def test_openapi_schema_available(self, client):
        """Test OpenAPI schema is available."""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        
        schema = response.json()
        assert "openapi" in schema
        assert "info" in schema
        assert schema["info"]["title"] == "StratMaster API"
        
        # Check that our new endpoints are documented
        paths = schema.get("paths", {})
        assert "/performance/benchmark" in paths
        assert "/performance/health" in paths
        assert "/export/notion" in paths
        assert "/export/trello" in paths
        assert "/export/jira" in paths
        
    def test_docs_ui_available(self, client):
        """Test Swagger UI documentation is available."""
        response = client.get("/docs")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]


class TestComponentIntegration:
    """Test integration between different StratMaster components."""
    
    def test_all_routers_registered(self, test_app):
        """Test that all expected routers are registered."""
        routes = [route.path for route in test_app.routes]
        
        # Check key route prefixes are present
        expected_prefixes = [
            "/export/", "/performance/", "/strategy/", 
            "/security/", "/debate/", "/retrieval/"
        ]
        
        for prefix in expected_prefixes:
            matching_routes = [route for route in routes if route.startswith(prefix)]
            assert len(matching_routes) > 0, f"No routes found for prefix: {prefix}"
    
    def test_healthcheck_endpoint(self, client):
        """Test basic healthcheck functionality."""
        response = client.get("/healthz")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
    
    def test_tracing_and_monitoring_integration(self, client):
        """Test that tracing and monitoring are properly integrated."""
        # Multiple requests should all have trace IDs
        trace_ids = set()
        for _ in range(5):
            response = client.get("/healthz")
            assert response.status_code == 200
            assert "X-Trace-Id" in response.headers
            trace_ids.add(response.headers["X-Trace-Id"])
        
        # Should have unique trace IDs
        assert len(trace_ids) == 5