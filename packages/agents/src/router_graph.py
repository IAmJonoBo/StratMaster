"""
Sprint 1 - Dynamic Agent Selection Router Graph

This module implements LangGraph-based routing to specialist agents based on
input classification, metadata, and policy flags.

The router uses conditional edges to route queries to:
- research: Web research and data collection
- knowledge: Vector search and knowledge retrieval  
- strategy: Business strategy formulation
- brand: Brand strategy and positioning
- ops: Operations and process optimization
"""

import os
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any

from langgraph.graph import StateGraph


class AgentType(Enum):
    """Available specialist agents for routing."""
    RESEARCH = "research"
    KNOWLEDGE = "knowledge"
    STRATEGY = "strategy"
    BRAND = "brand"
    OPS = "ops"


@dataclass
class RouterInput:
    """Input for the router graph."""
    query: str
    tenant_id: str
    metadata: dict[str, Any] | None = None
    policy_flags: dict[str, bool] | None = None


@dataclass
class RouterOutput:
    """Output from the router graph."""
    selected_agents: list[AgentType]
    rationale: str
    confidence: float
    routing_metadata: dict[str, Any]


class AgentRouter:
    """
    Lightweight agent router using rules and metadata classification.
    
    Routes queries to appropriate specialist agents based on:
    - Input metadata (detected entities, required tools)
    - Content classification (few-shot + rules)
    - Policy flags (verbose mode, fan-out restrictions)
    """
    
    def __init__(self):
        self.verbose = os.getenv("ROUTER_VERBOSE", "false").lower() == "true"
        self._setup_classification_rules()
    
    def _setup_classification_rules(self):
        """Setup rule-based classification patterns."""
        self.classification_patterns = {
            AgentType.RESEARCH: [
                r'\b(research|investigate|find|search|data|study|report)\b',
                r'\b(market|competitor|industry|trend|analysis)\b',
                r'\b(source|evidence|information|facts|statistics)\b'
            ],
            AgentType.KNOWLEDGE: [
                r'\b(explain|understand|knowledge|definition|concept)\b',
                r'\b(what is|how does|why|when|where)\b',
                r'\b(database|repository|knowledge base|vector)\b'
            ],
            AgentType.STRATEGY: [
                r'\b(strategy|strategic|plan|planning|roadmap)\b',
                r'\b(business|company|organization|enterprise)\b',
                r'\b(goal|objective|initiative|project|direction)\b'
            ],
            AgentType.BRAND: [
                r'\b(brand|branding|identity|positioning|perception)\b',
                r'\b(marketing|campaign|message|communication)\b',
                r'\b(customer|audience|segment|persona|experience)\b'
            ],
            AgentType.OPS: [
                r'\b(process|operation|workflow|procedure|system)\b',
                r'\b(efficiency|optimization|automation|improvement)\b',
                r'\b(deployment|infrastructure|monitoring|maintenance)\b'
            ]
        }
    
    def _classify_query(self, query: str) -> dict[AgentType, float]:
        """Classify query using rule-based patterns."""
        query_lower = query.lower()
        scores = {}
        
        for agent_type, patterns in self.classification_patterns.items():
            score = 0.0
            for pattern in patterns:
                matches = len(re.findall(pattern, query_lower))
                score += matches * 0.1  # Each match adds 0.1 to score
            
            # Normalize score by query length
            normalized_score = min(1.0, score / max(1, len(query.split()) * 0.05))
            scores[agent_type] = normalized_score
        
        return scores
    
    def _evaluate_metadata(self, metadata: dict[str, Any]) -> dict[AgentType, float]:
        """Evaluate metadata for routing hints."""
        if not metadata:
            return {}
        
        metadata_scores = {}
        
        # Check for detected entities
        entities = metadata.get("entities", [])
        if entities:
            for entity_type in entities:
                if entity_type in ["PERSON", "ORG", "PRODUCT"]:
                    metadata_scores[AgentType.BRAND] = metadata_scores.get(AgentType.BRAND, 0) + 0.2
                elif entity_type in ["DATE", "MONEY", "PERCENT"]:
                    metadata_scores[AgentType.STRATEGY] = metadata_scores.get(AgentType.STRATEGY, 0) + 0.2
        
        # Check for required tools
        required_tools = metadata.get("required_tools", [])
        if required_tools:
            for tool in required_tools:
                if tool in ["web_search", "crawl", "scrape"]:
                    metadata_scores[AgentType.RESEARCH] = metadata_scores.get(AgentType.RESEARCH, 0) + 0.3
                elif tool in ["vector_search", "knowledge_graph"]:
                    metadata_scores[AgentType.KNOWLEDGE] = metadata_scores.get(AgentType.KNOWLEDGE, 0) + 0.3
        
        # Check for domain context
        domain = metadata.get("domain", "")
        if domain:
            if domain in ["marketing", "advertising", "communications"]:
                metadata_scores[AgentType.BRAND] = metadata_scores.get(AgentType.BRAND, 0) + 0.3
            elif domain in ["operations", "devops", "infrastructure"]:
                metadata_scores[AgentType.OPS] = metadata_scores.get(AgentType.OPS, 0) + 0.3
        
        return metadata_scores
    
    def _apply_policy_flags(self, scores: dict[AgentType, float], policy_flags: dict[str, bool]) -> dict[AgentType, float]:
        """Apply policy flags to modify routing decisions."""
        if not policy_flags:
            return scores
        
        modified_scores = scores.copy()
        
        # Single agent mode - only select highest scoring agent
        if policy_flags.get("single_agent_mode", False):
            max_agent = max(scores.keys(), key=lambda k: scores[k])
            modified_scores = {agent: (1.0 if agent == max_agent else 0.0) for agent in scores.keys()}
        
        # Restrict specific agents
        if policy_flags.get("disable_research", False):
            modified_scores[AgentType.RESEARCH] = 0.0
        if policy_flags.get("disable_web_access", False):
            modified_scores[AgentType.RESEARCH] = 0.0
        
        # Boost specific agents
        if policy_flags.get("prefer_local_knowledge", False):
            modified_scores[AgentType.KNOWLEDGE] = modified_scores.get(AgentType.KNOWLEDGE, 0) + 0.2
        
        return modified_scores
    
    def route(self, router_input: RouterInput) -> RouterOutput:
        """
        Route a query to appropriate specialist agents.
        
        Returns selected agents with rationale and confidence scores.
        """
        # Step 1: Classify query content
        content_scores = self._classify_query(router_input.query)
        
        # Step 2: Evaluate metadata
        metadata_scores = self._evaluate_metadata(router_input.metadata or {})
        
        # Step 3: Combine scores
        combined_scores = {}
        for agent_type in AgentType:
            combined_scores[agent_type] = (
                content_scores.get(agent_type, 0.0) * 0.7 +  # Content classification weighted higher
                metadata_scores.get(agent_type, 0.0) * 0.3   # Metadata provides hints
            )
        
        # Step 4: Apply policy flags
        final_scores = self._apply_policy_flags(combined_scores, router_input.policy_flags or {})
        
        # Step 5: Select agents (threshold of 0.2 minimum)
        threshold = 0.2
        selected_agents = [
            agent_type for agent_type, score in final_scores.items() 
            if score >= threshold
        ]
        
        # Ensure at least one agent is selected (default to knowledge)
        if not selected_agents:
            selected_agents = [AgentType.KNOWLEDGE]
            final_scores[AgentType.KNOWLEDGE] = 0.5  # Default confidence
        
        # Step 6: Calculate overall confidence
        max_score = max(final_scores.values()) if final_scores else 0.5
        confidence = min(1.0, max_score)
        
        # Step 7: Generate rationale
        rationale_parts = []
        for agent in selected_agents:
            score = final_scores[agent]
            rationale_parts.append(f"{agent.value} (score: {score:.2f})")
        
        rationale = f"Selected agents: {', '.join(rationale_parts)}"
        
        if self.verbose:
            # Add detailed reasoning in verbose mode
            rationale += f". Content scores: {content_scores}. Metadata scores: {metadata_scores}."
        
        return RouterOutput(
            selected_agents=selected_agents,
            rationale=rationale,
            confidence=confidence,
            routing_metadata={
                "content_scores": content_scores,
                "metadata_scores": metadata_scores,
                "final_scores": final_scores,
                "threshold": threshold,
                "policy_flags": router_input.policy_flags or {}
            }
        )


def create_router_graph() -> StateGraph:
    """
    Create a LangGraph with routing logic.
    
    The graph has:
    - Router node that classifies and selects agents
    - Conditional edges to specialist agents
    - Fan-out capability based on policy
    """
    
    # Define the graph state
    class RouterState(dict):
        query: str
        tenant_id: str
        metadata: dict[str, Any] | None
        policy_flags: dict[str, bool] | None
        selected_agents: list[str] | None
        rationale: str | None
        confidence: float | None
        routing_metadata: dict[str, Any] | None
    
    # Create the router instance
    router = AgentRouter()
    
    def router_node(state: RouterState) -> RouterState:
        """Main router node that selects appropriate agents."""
        router_input = RouterInput(
            query=state["query"],
            tenant_id=state["tenant_id"],
            metadata=state.get("metadata"),
            policy_flags=state.get("policy_flags")
        )
        
        result = router.route(router_input)
        
        return {
            **state,
            "selected_agents": [agent.value for agent in result.selected_agents],
            "rationale": result.rationale,
            "confidence": result.confidence,
            "routing_metadata": result.routing_metadata
        }
    
    # Conditional edge functions for each agent type
    def should_route_to_research(state: RouterState) -> bool:
        return "research" in (state.get("selected_agents") or [])
    
    def should_route_to_knowledge(state: RouterState) -> bool:
        return "knowledge" in (state.get("selected_agents") or [])
    
    def should_route_to_strategy(state: RouterState) -> bool:
        return "strategy" in (state.get("selected_agents") or [])
    
    def should_route_to_brand(state: RouterState) -> bool:
        return "brand" in (state.get("selected_agents") or [])
    
    def should_route_to_ops(state: RouterState) -> bool:
        return "ops" in (state.get("selected_agents") or [])
    
    # Create the graph
    graph = StateGraph(RouterState)
    
    # Add the router node
    graph.add_node("router", router_node)
    
    # Set router as entry point
    graph.set_entry_point("router")
    
    # Add conditional edges to specialist agents
    graph.add_conditional_edges(
        "router",
        {
            "research": should_route_to_research,
            "knowledge": should_route_to_knowledge,
            "strategy": should_route_to_strategy,
            "brand": should_route_to_brand,
            "ops": should_route_to_ops,
            "END": lambda state: True  # Always allow ending
        }
    )
    
    # Add specialist agent nodes (stubs for now)
    def research_node(state: RouterState) -> RouterState:
        return {**state, "research_result": "Research completed"}
    
    def knowledge_node(state: RouterState) -> RouterState:
        return {**state, "knowledge_result": "Knowledge retrieved"}
    
    def strategy_node(state: RouterState) -> RouterState:
        return {**state, "strategy_result": "Strategy formulated"}
    
    def brand_node(state: RouterState) -> RouterState:
        return {**state, "brand_result": "Brand strategy developed"}
    
    def ops_node(state: RouterState) -> RouterState:
        return {**state, "ops_result": "Operations optimized"}
    
    graph.add_node("research", research_node)
    graph.add_node("knowledge", knowledge_node)
    graph.add_node("strategy", strategy_node)
    graph.add_node("brand", brand_node)
    graph.add_node("ops", ops_node)
    
    # All specialist nodes lead to END
    for agent in ["research", "knowledge", "strategy", "brand", "ops"]:
        graph.add_edge(agent, "END")
    
    return graph


# Export the main classes and functions
__all__ = [
    "AgentType",
    "RouterInput", 
    "RouterOutput",
    "AgentRouter",
    "create_router_graph"
]