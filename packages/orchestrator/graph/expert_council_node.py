"""LangGraph node for Expert Council evaluation stage."""

from __future__ import annotations

import logging
from typing import Any

# This would normally import from langgraph but we'll keep it simple for now
# from langgraph.checkpoint import MemorySaver

logger = logging.getLogger(__name__)


class ExpertCouncilNode:
    """LangGraph node that integrates Expert Council evaluation into the workflow."""
    
    def __init__(self, mcp_client: Any = None):
        """Initialize the Expert Council node.
        
        Args:
            mcp_client: MCP client for communicating with expertise-mcp server
        """
        self.mcp_client = mcp_client
        self.default_disciplines = ["psychology", "design", "communication", "brand_science"]
        self.default_weights = {
            "psychology": 0.3,
            "design": 0.3, 
            "communication": 0.2,
            "brand_science": 0.2
        }
    
    async def __call__(self, state: dict[str, Any]) -> dict[str, Any]:
        """Execute the Expert Council evaluation stage.
        
        Args:
            state: Current workflow state containing strategy data
            
        Returns:
            Updated state with expert evaluation results
        """
        logger.info("Starting Expert Council evaluation")
        
        # Extract strategy from state
        strategy = state.get("strategy", {})
        if not strategy:
            logger.warning("No strategy found in state")
            return state
        
        # Get disciplines to evaluate (from config or defaults)
        disciplines = state.get("expert_disciplines", self.default_disciplines)
        weights = state.get("expert_weights", self.default_weights)
        
        try:
            # Step 1: Evaluate strategy across disciplines
            if self.mcp_client:
                eval_result = await self.mcp_client.call("expert.evaluate", {
                    "strategy": strategy,
                    "disciplines": disciplines
                })
                memos = eval_result
            else:
                # Fallback for when MCP client is not available
                logger.warning("No MCP client available, using stub evaluation")
                memos = self._stub_evaluation(strategy, disciplines)
            
            # Step 2: Aggregate into council vote
            if self.mcp_client:
                vote_result = await self.mcp_client.call("expert.vote", {
                    "strategy_id": strategy.get("id", "unknown"),
                    "weights": weights,
                    "memos": memos
                })
                council_vote = vote_result
            else:
                # Fallback for when MCP client is not available
                council_vote = self._stub_vote(strategy.get("id", "unknown"), weights, memos)
            
            # Update state with expert evaluation results
            state["expert_memos"] = memos
            state["expert_council_vote"] = council_vote
            state["expert_score"] = council_vote.get("weighted_score", 0.0)
            
            # Check if score meets threshold (could block further stages)
            threshold = state.get("expert_threshold", 0.6)
            if council_vote.get("weighted_score", 0.0) < threshold:
                state["expert_evaluation_passed"] = False
                logger.warning(f"Expert evaluation score {council_vote.get('weighted_score', 0.0)} below threshold {threshold}")
            else:
                state["expert_evaluation_passed"] = True
                logger.info(f"Expert evaluation passed with score {council_vote.get('weighted_score', 0.0)}")
            
        except Exception as e:
            logger.error(f"Expert Council evaluation failed: {e}")
            state["expert_evaluation_error"] = str(e)
            state["expert_evaluation_passed"] = False
        
        logger.info("Expert Council evaluation complete")
        return state
    
    def _stub_evaluation(self, strategy: dict[str, Any], disciplines: list[str]) -> list[dict[str, Any]]:
        """Stub evaluation for when MCP client is unavailable."""
        memos = []
        for discipline in disciplines:
            memo = {
                "id": f"memo:{discipline}",
                "discipline": discipline,
                "applies_to": strategy.get("id", "unknown"),
                "findings": [{
                    "id": f"{discipline}_stub",
                    "severity": "info",
                    "title": f"Stub evaluation for {discipline}",
                    "description": "MCP client not available, using placeholder evaluation"
                }],
                "scores": {"overall": 0.5},  # Neutral score
                "recommendations": [f"Implement proper {discipline} evaluation"]
            }
            memos.append(memo)
        return memos
    
    def _stub_vote(self, strategy_id: str, weights: dict[str, float], memos: list[dict[str, Any]]) -> dict[str, Any]:
        """Stub vote aggregation for when MCP client is unavailable."""
        votes = []
        total_score = 0.0
        total_weight = 0.0
        
        for memo in memos:
            discipline = memo["discipline"]
            score = memo["scores"].get("overall", 0.0)
            weight = weights.get(discipline, 0.0)
            
            votes.append({
                "id": f"vote:{discipline}",
                "discipline": discipline,
                "score": score
            })
            
            total_score += score * weight
            total_weight += weight
        
        weighted_score = total_score / total_weight if total_weight > 0 else 0.0
        
        return {
            "id": f"vote:{strategy_id}",
            "strategy_id": strategy_id,
            "votes": votes,
            "weighted_score": weighted_score,
            "weights": weights
        }


def create_expert_council_node(mcp_client: Any = None) -> ExpertCouncilNode:
    """Factory function to create an Expert Council node.
    
    Args:
        mcp_client: MCP client for expertise-mcp server
        
    Returns:
        Configured ExpertCouncilNode instance
    """
    return ExpertCouncilNode(mcp_client=mcp_client)


__all__ = ["ExpertCouncilNode", "create_expert_council_node"]