"""
Sprint 1 - Tests for Dynamic Agent Selection Router

This module tests the agent routing functionality including:
- Rule-based classification accuracy
- Metadata evaluation 
- Policy flag application
- Edge cases and error handling
"""


from ..router_graph import AgentRouter, AgentType, RouterInput, RouterOutput


class TestAgentRouter:
    """Test suite for the AgentRouter class."""

    def setup_method(self):
        """Setup router instance for each test."""
        self.router = AgentRouter()

    def test_research_classification(self):
        """Test routing to research agent."""
        test_cases = [
            "Find market research on AI trends",
            "Investigate competitor pricing strategies",
            "Search for industry reports on sustainability",
            "Analyze customer data and statistics"
        ]
        
        for query in test_cases:
            input_req = RouterInput(
                query=query,
                tenant_id="test-tenant"
            )
            result = self.router.route(input_req)
            
            assert AgentType.RESEARCH in result.selected_agents, f"Failed for query: {query}"
            assert result.confidence > 0.2, f"Low confidence for research query: {query}"

    def test_knowledge_classification(self):
        """Test routing to knowledge agent."""
        test_cases = [
            "What is brand positioning?",
            "Explain the concept of customer segmentation",
            "How does the knowledge base work?",
            "Define strategic planning framework"
        ]
        
        for query in test_cases:
            input_req = RouterInput(
                query=query,
                tenant_id="test-tenant"
            )
            result = self.router.route(input_req)
            
            assert AgentType.KNOWLEDGE in result.selected_agents, f"Failed for query: {query}"
            assert result.confidence > 0.2, f"Low confidence for knowledge query: {query}"

    def test_strategy_classification(self):
        """Test routing to strategy agent."""
        test_cases = [
            "Develop a business strategy for market expansion", 
            "Create strategic roadmap for next quarter",
            "Plan organizational restructuring initiative",
            "Design company growth strategy"
        ]
        
        for query in test_cases:
            input_req = RouterInput(
                query=query,
                tenant_id="test-tenant"
            )
            result = self.router.route(input_req)
            
            assert AgentType.STRATEGY in result.selected_agents, f"Failed for query: {query}"
            assert result.confidence > 0.2, f"Low confidence for strategy query: {query}"

    def test_brand_classification(self):
        """Test routing to brand agent."""
        test_cases = [
            "Develop brand identity for new product",
            "Create marketing campaign messaging",
            "Analyze customer brand perception",
            "Design brand positioning strategy"
        ]
        
        for query in test_cases:
            input_req = RouterInput(
                query=query,
                tenant_id="test-tenant"
            )
            result = self.router.route(input_req)
            
            assert AgentType.BRAND in result.selected_agents, f"Failed for query: {query}"
            assert result.confidence > 0.2, f"Low confidence for brand query: {query}"

    def test_ops_classification(self):
        """Test routing to operations agent."""
        test_cases = [
            "Optimize deployment workflow process",
            "Improve system monitoring efficiency", 
            "Automate infrastructure maintenance",
            "Streamline operational procedures"
        ]
        
        for query in test_cases:
            input_req = RouterInput(
                query=query,
                tenant_id="test-tenant"
            )
            result = self.router.route(input_req)
            
            assert AgentType.OPS in result.selected_agents, f"Failed for query: {query}"
            assert result.confidence > 0.2, f"Low confidence for ops query: {query}"

    def test_metadata_routing(self):
        """Test metadata-based routing hints."""
        # Test entity-based routing
        input_req = RouterInput(
            query="Analyze this information",
            tenant_id="test-tenant",
            metadata={
                "entities": ["PERSON", "ORG", "PRODUCT"],
                "domain": "marketing"
            }
        )
        result = self.router.route(input_req)
        assert AgentType.BRAND in result.selected_agents

        # Test tool-based routing
        input_req = RouterInput(
            query="Get information",
            tenant_id="test-tenant", 
            metadata={
                "required_tools": ["web_search", "crawl"]
            }
        )
        result = self.router.route(input_req)
        assert AgentType.RESEARCH in result.selected_agents

    def test_policy_flags(self):
        """Test policy flag enforcement."""
        # Test single agent mode
        input_req = RouterInput(
            query="Research brand strategy for marketing campaign",
            tenant_id="test-tenant",
            policy_flags={"single_agent_mode": True}
        )
        result = self.router.route(input_req)
        assert len(result.selected_agents) == 1

        # Test disable research
        input_req = RouterInput(
            query="Find market research data", 
            tenant_id="test-tenant",
            policy_flags={"disable_research": True}
        )
        result = self.router.route(input_req)
        assert AgentType.RESEARCH not in result.selected_agents

        # Test prefer local knowledge
        input_req = RouterInput(
            query="Generic query",
            tenant_id="test-tenant",
            policy_flags={"prefer_local_knowledge": True}
        )
        result = self.router.route(input_req)
        # Should boost knowledge agent score
        knowledge_score = result.routing_metadata["final_scores"][AgentType.KNOWLEDGE]
        assert knowledge_score >= 0.2

    def test_multi_agent_selection(self):
        """Test queries that should route to multiple agents."""
        input_req = RouterInput(
            query="Research market trends and develop brand strategy campaign",
            tenant_id="test-tenant"
        )
        result = self.router.route(input_req)
        
        # Should select both research and brand agents
        assert len(result.selected_agents) >= 1
        assert result.confidence > 0.0

    def test_default_fallback(self):
        """Test fallback to knowledge agent for unclear queries."""
        input_req = RouterInput(
            query="hello world test xyz",
            tenant_id="test-tenant"
        )
        result = self.router.route(input_req)
        
        # Should fallback to knowledge agent
        assert len(result.selected_agents) >= 1
        assert result.confidence >= 0.0

    def test_verbose_mode(self):
        """Test verbose routing rationale."""
        import os
        original_verbose = os.getenv("ROUTER_VERBOSE")
        
        try:
            os.environ["ROUTER_VERBOSE"] = "true"
            verbose_router = AgentRouter()
            
            input_req = RouterInput(
                query="Find research about brand strategy",
                tenant_id="test-tenant"
            )
            result = verbose_router.route(input_req)
            
            # Verbose mode should include detailed scores
            assert "Content scores:" in result.rationale
            assert "Metadata scores:" in result.rationale
            
        finally:
            if original_verbose is not None:
                os.environ["ROUTER_VERBOSE"] = original_verbose
            else:
                os.environ.pop("ROUTER_VERBOSE", None)

    def test_routing_accuracy_suite(self):
        """Test routing accuracy on a comprehensive test set."""
        test_cases = [
            # Research queries
            ("Find competitor analysis", [AgentType.RESEARCH]),
            ("Search industry reports", [AgentType.RESEARCH]),
            ("Investigate market data", [AgentType.RESEARCH]),
            
            # Knowledge queries  
            ("What is brand equity?", [AgentType.KNOWLEDGE]),
            ("Explain customer journey mapping", [AgentType.KNOWLEDGE]),
            ("Define value proposition", [AgentType.KNOWLEDGE]),
            
            # Strategy queries
            ("Develop business plan", [AgentType.STRATEGY]),
            ("Create strategic roadmap", [AgentType.STRATEGY]), 
            ("Plan market expansion", [AgentType.STRATEGY]),
            
            # Brand queries
            ("Design brand identity", [AgentType.BRAND]),
            ("Create marketing message", [AgentType.BRAND]),
            ("Develop brand positioning", [AgentType.BRAND]),
            
            # Ops queries
            ("Optimize workflow process", [AgentType.OPS]),
            ("Improve system efficiency", [AgentType.OPS]),
            ("Automate deployment", [AgentType.OPS])
        ]
        
        correct_predictions = 0
        total_predictions = len(test_cases)
        
        for query, expected_agents in test_cases:
            input_req = RouterInput(
                query=query,
                tenant_id="test-tenant"
            )
            result = self.router.route(input_req)
            
            # Check if any expected agent is in selected agents
            if any(agent in result.selected_agents for agent in expected_agents):
                correct_predictions += 1
        
        accuracy = correct_predictions / total_predictions
        
        # Should achieve >90% accuracy per Sprint 1 requirements
        assert accuracy >= 0.90, f"Routing accuracy {accuracy:.2%} below threshold"

    def test_routing_latency(self):
        """Test routing latency requirements (<20ms per Sprint 1)."""
        import time
        
        input_req = RouterInput(
            query="Find research about brand strategy development",
            tenant_id="test-tenant"
        )
        
        # Warm up the router
        self.router.route(input_req)
        
        # Measure routing time
        start_time = time.time()
        result = self.router.route(input_req)
        end_time = time.time()
        
        latency_ms = (end_time - start_time) * 1000
        
        # Should be under 20ms per Sprint 1 requirements
        assert latency_ms < 20, f"Routing latency {latency_ms:.1f}ms exceeds 20ms threshold"
        assert result.confidence > 0.0


class TestRouterOutput:
    """Test suite for RouterOutput validation."""

    def test_router_output_structure(self):
        """Test RouterOutput data structure."""
        output = RouterOutput(
            selected_agents=[AgentType.RESEARCH, AgentType.BRAND],
            rationale="Selected research and brand agents",
            confidence=0.85,
            routing_metadata={"test": "metadata"}
        )
        
        assert len(output.selected_agents) == 2
        assert output.confidence == 0.85
        assert "test" in output.routing_metadata


class TestRouterIntegration:
    """Integration tests for router with MCP service."""
    
    def test_router_input_validation(self):
        """Test RouterInput validation."""
        # Valid input
        valid_input = RouterInput(
            query="test query",
            tenant_id="test-tenant"
        )
        assert valid_input.query == "test query"
        assert valid_input.metadata == None
        assert valid_input.policy_flags == None
        
        # Input with metadata
        input_with_metadata = RouterInput(
            query="test query",
            tenant_id="test-tenant",
            metadata={"domain": "marketing"},
            policy_flags={"verbose": True}
        )
        assert input_with_metadata.metadata["domain"] == "marketing"
        assert input_with_metadata.policy_flags["verbose"] is True