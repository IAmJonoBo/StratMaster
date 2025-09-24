"""
Sprint 2: Learning from Debates
AI system that learns from debate outcomes and improves policy decisions.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

logger = logging.getLogger(__name__)


class DebateOutcome:
    """Represents a debate outcome for learning."""
    
    def __init__(
        self,
        debate_id: str,
        outcome: str,  # "accepted", "rejected", "escalated"
        confidence: float,
        quality_rating: int | None,
        human_feedback: str | None,
        debate_features: dict[str, Any],
        timestamp: datetime | None = None
    ):
        self.debate_id = debate_id
        self.outcome = outcome
        self.confidence = confidence
        self.quality_rating = quality_rating
        self.human_feedback = human_feedback
        self.debate_features = debate_features
        self.timestamp = timestamp or datetime.now(timezone.utc)


class DebateLearningSystem:
    """ML system that learns from debate outcomes to improve future decisions."""
    
    def __init__(self):
        self.outcomes: list[DebateOutcome] = []
        self.model: Pipeline | None = None
        self.feature_extractor = TfidfVectorizer(max_features=1000, stop_words='english')
        self.classifier = LogisticRegression(random_state=42)
        self.is_trained = False
        self.training_threshold = 10  # Minimum outcomes needed for training
        
    def record_outcome(self, outcome: DebateOutcome) -> None:
        """Record a debate outcome for learning."""
        self.outcomes.append(outcome)
        logger.info(f"Recorded debate outcome: {outcome.debate_id} -> {outcome.outcome}")
        
        # Auto-retrain if we have enough data
        if len(self.outcomes) >= self.training_threshold:
            self._retrain_model()
    
    def extract_features(self, debate_data: dict[str, Any]) -> dict[str, Any]:
        """Extract features from debate data for ML training."""
        features = {}
        
        # Text-based features
        if "hypothesis" in debate_data:
            features["hypothesis_length"] = len(debate_data["hypothesis"])
            features["hypothesis_confidence_words"] = self._count_confidence_words(
                debate_data["hypothesis"]
            )
        
        # Participant features
        participants = debate_data.get("participants", [])
        features["participant_count"] = len(participants)
        features["has_research_agent"] = "research" in participants
        features["has_strategy_agent"] = "strategy" in participants
        
        # Debate dynamics
        turns = debate_data.get("turns", [])
        features["turn_count"] = len(turns)
        if turns:
            features["avg_turn_length"] = sum(len(turn.get("content", "")) for turn in turns) / len(turns)
            features["agreement_ratio"] = self._calculate_agreement_ratio(turns)
        
        # Evidence features
        evidence = debate_data.get("evidence", [])
        features["evidence_count"] = len(evidence)
        features["high_confidence_evidence"] = sum(
            1 for e in evidence if e.get("confidence", 0) > 0.8
        )
        
        # Timing features
        if "duration_minutes" in debate_data:
            features["duration_minutes"] = debate_data["duration_minutes"]
        
        return features
    
    def _count_confidence_words(self, text: str) -> int:
        """Count confidence-indicating words in text."""
        confidence_words = [
            "certain", "confident", "proven", "validated", "clear", "evident",
            "definitely", "absolutely", "undoubtedly", "surely"
        ]
        return sum(1 for word in confidence_words if word in text.lower())
    
    def _calculate_agreement_ratio(self, turns: list[dict[str, Any]]) -> float:
        """Calculate ratio of agreement vs disagreement in debate turns."""
        if not turns:
            return 0.5
        
        agreement_words = ["agree", "correct", "yes", "accurate", "valid", "right"]
        disagreement_words = ["disagree", "wrong", "no", "incorrect", "invalid", "false"]
        
        agreement_count = 0
        disagreement_count = 0
        
        for turn in turns:
            content = turn.get("content", "").lower()
            agreement_count += sum(1 for word in agreement_words if word in content)
            disagreement_count += sum(1 for word in disagreement_words if word in content)
        
        total = agreement_count + disagreement_count
        return agreement_count / total if total > 0 else 0.5
    
    def _retrain_model(self) -> None:
        """Retrain the ML model with accumulated outcomes."""
        if len(self.outcomes) < self.training_threshold:
            logger.info(f"Not enough data for training ({len(self.outcomes)} < {self.training_threshold})")
            return
        
        try:
            # Prepare training data
            X = []  # Features
            y = []  # Labels
            
            for outcome in self.outcomes:
                features = self.extract_features(outcome.debate_features)
                
                # Convert features to text for TF-IDF (combine with hypothesis if available)
                text_features = []
                if "hypothesis" in outcome.debate_features:
                    text_features.append(outcome.debate_features["hypothesis"])
                if outcome.human_feedback:
                    text_features.append(outcome.human_feedback)
                
                text = " ".join(text_features) if text_features else "no_text"
                X.append(text)
                
                # Convert outcome to binary classification (accepted=1, others=0)
                y.append(1 if outcome.outcome == "accepted" else 0)
            
            # Create and train pipeline
            self.model = Pipeline([
                ('tfidf', self.feature_extractor),
                ('classifier', self.classifier)
            ])
            
            self.model.fit(X, y)
            self.is_trained = True
            
            # Calculate training accuracy
            train_accuracy = self.model.score(X, y)
            logger.info(f"Model retrained with {len(self.outcomes)} outcomes, accuracy: {train_accuracy:.3f}")
            
        except Exception as e:
            logger.error(f"Failed to retrain model: {e}")
    
    def predict_outcome(self, debate_data: dict[str, Any]) -> dict[str, Any]:
        """Predict likely outcome for a debate."""
        if not self.is_trained:
            return {
                "prediction": "unknown",
                "confidence": 0.5,
                "recommendations": ["Insufficient training data for prediction"]
            }
        
        try:
            # Prepare input
            text_features = []
            if "hypothesis" in debate_data:
                text_features.append(debate_data["hypothesis"])
            
            text = " ".join(text_features) if text_features else "no_text"
            
            # Make prediction
            prediction_proba = self.model.predict_proba([text])[0]
            predicted_class = self.model.predict([text])[0]
            
            # Generate recommendations
            features = self.extract_features(debate_data)
            recommendations = self._generate_recommendations(features, prediction_proba)
            
            return {
                "prediction": "accepted" if predicted_class == 1 else "needs_improvement",
                "confidence": float(max(prediction_proba)),
                "acceptance_probability": float(prediction_proba[1]),
                "recommendations": recommendations
            }
            
        except Exception as e:
            logger.error(f"Prediction failed: {e}")
            return {
                "prediction": "error",
                "confidence": 0.0,
                "recommendations": ["Prediction system temporarily unavailable"]
            }
    
    def _generate_recommendations(
        self, features: dict[str, Any], prediction_proba: list[float]
    ) -> list[str]:
        """Generate actionable recommendations based on features and prediction."""
        recommendations = []
        
        acceptance_prob = prediction_proba[1] if len(prediction_proba) > 1 else 0.5
        
        if acceptance_prob < 0.6:
            if features.get("evidence_count", 0) < 3:
                recommendations.append("Gather more supporting evidence")
            
            if features.get("turn_count", 0) > 10:
                recommendations.append("Consider shortening debate to improve focus")
            
            if features.get("agreement_ratio", 0.5) < 0.3:
                recommendations.append("Address major disagreements before proceeding")
            
            if features.get("hypothesis_confidence_words", 0) < 2:
                recommendations.append("Strengthen hypothesis with more confident language")
        
        if features.get("participant_count", 0) < 2:
            recommendations.append("Include diverse perspectives for better outcomes")
        
        if not features.get("has_research_agent", False):
            recommendations.append("Include research agent for evidence validation")
        
        return recommendations[:5]  # Limit to top 5 recommendations
    
    def get_learning_metrics(self) -> dict[str, Any]:
        """Get metrics about the learning system performance."""
        if not self.outcomes:
            return {"status": "no_data", "total_outcomes": 0}
        
        metrics = {
            "total_outcomes": len(self.outcomes),
            "is_trained": self.is_trained,
            "training_threshold": self.training_threshold
        }
        
        # Outcome distribution
        outcome_counts = {}
        quality_ratings = []
        
        for outcome in self.outcomes:
            outcome_counts[outcome.outcome] = outcome_counts.get(outcome.outcome, 0) + 1
            if outcome.quality_rating:
                quality_ratings.append(outcome.quality_rating)
        
        metrics["outcome_distribution"] = outcome_counts
        
        if quality_ratings:
            metrics["average_quality_rating"] = sum(quality_ratings) / len(quality_ratings)
            metrics["quality_trend"] = self._calculate_quality_trend()
        
        if self.is_trained:
            metrics["model_performance"] = self._evaluate_model_performance()
        
        return metrics
    
    def _calculate_quality_trend(self) -> str:
        """Calculate trend in debate quality over time."""
        if len(self.outcomes) < 5:
            return "insufficient_data"
        
        # Get recent vs older outcomes
        sorted_outcomes = sorted(self.outcomes, key=lambda x: x.timestamp)
        recent_count = len(sorted_outcomes) // 3
        
        recent_ratings = [
            o.quality_rating for o in sorted_outcomes[-recent_count:]
            if o.quality_rating is not None
        ]
        older_ratings = [
            o.quality_rating for o in sorted_outcomes[:recent_count]
            if o.quality_rating is not None
        ]
        
        if not recent_ratings or not older_ratings:
            return "insufficient_ratings"
        
        recent_avg = sum(recent_ratings) / len(recent_ratings)
        older_avg = sum(older_ratings) / len(older_ratings)
        
        diff = recent_avg - older_avg
        if diff > 0.2:
            return "improving"
        elif diff < -0.2:
            return "declining"
        else:
            return "stable"
    
    def _evaluate_model_performance(self) -> dict[str, float]:
        """Evaluate current model performance on historical data."""
        if not self.is_trained or len(self.outcomes) < 5:
            return {}
        
        try:
            # Use recent outcomes for validation
            validation_outcomes = self.outcomes[-5:]
            
            X_val = []
            y_true = []
            
            for outcome in validation_outcomes:
                text_features = []
                if "hypothesis" in outcome.debate_features:
                    text_features.append(outcome.debate_features["hypothesis"])
                if outcome.human_feedback:
                    text_features.append(outcome.human_feedback)
                
                text = " ".join(text_features) if text_features else "no_text"
                X_val.append(text)
                y_true.append(1 if outcome.outcome == "accepted" else 0)
            
            y_pred = self.model.predict(X_val)
            y_proba = self.model.predict_proba(X_val)
            
            # Calculate metrics
            accuracy = sum(1 for i in range(len(y_true)) if y_true[i] == y_pred[i]) / len(y_true)
            avg_confidence = float(sum(max(proba) for proba in y_proba) / len(y_proba))
            
            return {
                "validation_accuracy": accuracy,
                "average_confidence": avg_confidence,
                "validation_samples": len(validation_outcomes)
            }
            
        except Exception as e:
            logger.error(f"Model evaluation failed: {e}")
            return {"error": str(e)}


# Global learning system instance
debate_learning_system = DebateLearningSystem()