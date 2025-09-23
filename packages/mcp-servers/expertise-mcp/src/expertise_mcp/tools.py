"""Core evaluation tools for expert disciplines."""

from __future__ import annotations

import logging
from typing import Any

from packages.api.src.stratmaster_api.models.experts.memo import DisciplineMemo, Finding
from packages.api.src.stratmaster_api.models.experts.vote import CouncilVote, DisciplineVote

from .adapters.doctrine_loader import load_doctrines
from .adapters.checkers import run_checks_for_discipline

logger = logging.getLogger(__name__)


def evaluate(strategy: dict[str, Any], disciplines: list[str]) -> list[DisciplineMemo]:
    """Evaluate a strategy across multiple expert disciplines.
    
    Args:
        strategy: Strategy data to evaluate
        disciplines: List of discipline names to evaluate against
        
    Returns:
        List of discipline memos with findings and scores
    """
    logger.info(f"Evaluating strategy {strategy.get('id', 'unknown')} across {len(disciplines)} disciplines")
    
    docs = load_doctrines()
    memos: list[DisciplineMemo] = []
    
    for discipline in disciplines:
        try:
            findings_data, scores, recs = run_checks_for_discipline(discipline, strategy, docs)
            
            # Convert findings data to Finding objects
            findings = [Finding(**f) for f in findings_data]
            
            memo = DisciplineMemo(
                id=f"memo:{discipline}",
                discipline=discipline,
                applies_to=strategy.get("id", "unknown"),
                findings=findings,
                scores=scores,
                recommendations=recs
            )
            memos.append(memo)
            
        except Exception as e:
            logger.error(f"Failed to evaluate discipline {discipline}: {e}")
            # Create error memo
            error_memo = DisciplineMemo(
                id=f"memo:{discipline}:error",
                discipline=discipline,
                applies_to=strategy.get("id", "unknown"),
                findings=[Finding(
                    id=f"{discipline}_error",
                    severity="error",
                    title=f"Evaluation failed for {discipline}",
                    description=f"Error during evaluation: {str(e)}"
                )],
                scores={"overall": 0.0, "error": 1.0},
                recommendations=[f"Fix evaluation system for {discipline}"]
            )
            memos.append(error_memo)
    
    logger.info(f"Generated {len(memos)} discipline memos")
    return memos


def vote(strategy_id: str, weights: dict[str, float], memos: list[DisciplineMemo]) -> CouncilVote:
    """Aggregate discipline memos into a weighted council vote.
    
    Args:
        strategy_id: ID of the strategy being voted on
        weights: Weights for each discipline
        memos: List of discipline memos to aggregate
        
    Returns:
        Council vote with weighted scores
    """
    logger.info(f"Aggregating votes for strategy {strategy_id} from {len(memos)} memos")
    
    votes = []
    total_weighted_score = 0.0
    total_weights = 0.0
    
    for memo in memos:
        # Get overall score for this discipline
        overall_score = float(memo.scores.get("overall", 0.0))
        discipline_weight = float(weights.get(memo.discipline, 0.0))
        
        # Create discipline vote
        discipline_vote = DisciplineVote(
            id=f"vote:{memo.discipline}",
            discipline=memo.discipline,
            score=overall_score
        )
        votes.append(discipline_vote)
        
        # Add to weighted total
        total_weighted_score += overall_score * discipline_weight
        total_weights += discipline_weight
    
    # Calculate final weighted score
    final_score = total_weighted_score / total_weights if total_weights > 0 else 0.0
    
    council_vote = CouncilVote(
        id=f"vote:{strategy_id}",
        strategy_id=strategy_id,
        votes=votes,
        weighted_score=final_score,
        weights=weights
    )
    
    logger.info(f"Council vote complete: {final_score:.2f} from {len(votes)} disciplines")
    return council_vote


__all__ = ["evaluate", "vote"]