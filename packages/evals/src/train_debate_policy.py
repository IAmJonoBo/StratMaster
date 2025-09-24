"""
Sprint 2 - Debate Policy Trainer

This module implements an offline trainer that learns from logged debate outcomes
to predict when debates add value vs when single-agent responses suffice.

The trainer uses scikit-learn to build a lightweight policy model that can make
sub-3ms predictions on whether to:
- Use single agent 
- Use 2-agent debate
- Use full adversarial debate rounds

Features extracted from debate outcomes:
- Task complexity (token count, entity count)
- Historical acceptance rates for tenant/agent combinations
- Evidence quality metrics
- Latency vs quality trade-offs
"""

import pickle
import json
import sqlite3
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report, accuracy_score
from sklearn.preprocessing import StandardScaler


@dataclass
class DebateFeatures:
    """Features extracted from a debate request for policy prediction."""
    
    # Task features
    query_length: int
    estimated_complexity: float  # 0-1 scale based on query analysis
    entity_count: int
    domain: str
    
    # Historical features (tenant-specific)
    tenant_avg_acceptance_rate: float
    tenant_avg_debate_latency: float
    tenant_avg_single_agent_quality: float
    
    # Agent features
    preferred_agents: List[str]
    agent_compatibility_score: float  # How well these agents work together
    
    # Context features
    time_pressure: bool  # Whether this is a time-sensitive request
    quality_threshold: float  # Required quality level (0-1)


@dataclass
class DebateOutcomeRecord:
    """Outcome record for training the policy model."""
    
    task_id: str
    tenant_id: str
    agents: List[str]
    evidence_count: int
    citations_ok: bool
    critique_count: int
    user_acceptance: str  # "accepted", "revised", "rejected"
    latency_ms: float
    cost_tokens: int
    timestamp: datetime
    
    # Derived features
    quality_score: float  # Computed from acceptance + citations
    efficiency_score: float  # Quality per token spent
    
    # Labels for training
    was_debate_beneficial: bool  # Whether debate improved over single-agent
    optimal_agent_count: int  # Ideal number of agents for this task


class DebatePolicyTrainer:
    """
    Offline trainer for debate policy learning.
    
    Uses logged debate outcomes to learn when debates add value vs cost.
    Produces a lightweight model for real-time inference during routing.
    """
    
    def __init__(self, data_path: Optional[Path] = None):
        self.data_path = data_path or Path("data/debate_outcomes.db")
        self.model_path = Path("models/debate_policy.pkl")
        self.scaler_path = Path("models/debate_scaler.pkl")
        
        # Ensure directories exist
        self.model_path.parent.mkdir(exist_ok=True)
        
        # Models
        self.classifier = GradientBoostingClassifier(
            n_estimators=100,
            learning_rate=0.1,
            max_depth=3,
            random_state=42
        )
        self.scaler = StandardScaler()
        
    def load_debate_outcomes(self) -> List[DebateOutcomeRecord]:
        """Load debate outcomes from SQLite database."""
        if not self.data_path.exists():
            print(f"No data file found at {self.data_path}. Generating synthetic data for demo.")
            return self._generate_synthetic_data()
        
        outcomes = []
        
        with sqlite3.connect(self.data_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT task_id, tenant_id, agents, evidence_count, citations_ok,
                       critique_count, user_acceptance, latency_ms, cost_tokens, timestamp
                FROM debate_outcomes
                ORDER BY timestamp DESC
            """)
            
            for row in cursor.fetchall():
                task_id, tenant_id, agents_json, evidence_count, citations_ok, \
                critique_count, user_acceptance, latency_ms, cost_tokens, timestamp_str = row
                
                agents = json.loads(agents_json)
                timestamp = datetime.fromisoformat(timestamp_str)
                
                # Compute derived features
                quality_score = self._compute_quality_score(user_acceptance, citations_ok, evidence_count)
                efficiency_score = quality_score / max(1, cost_tokens / 1000)  # Quality per 1k tokens
                
                # Determine labels
                was_beneficial = self._was_debate_beneficial(quality_score, len(agents), cost_tokens)
                optimal_count = self._compute_optimal_agent_count(quality_score, latency_ms, cost_tokens)
                
                outcomes.append(DebateOutcomeRecord(
                    task_id=task_id,
                    tenant_id=tenant_id,
                    agents=agents,
                    evidence_count=evidence_count,
                    citations_ok=citations_ok,
                    critique_count=critique_count,
                    user_acceptance=user_acceptance,
                    latency_ms=latency_ms,
                    cost_tokens=cost_tokens,
                    timestamp=timestamp,
                    quality_score=quality_score,
                    efficiency_score=efficiency_score,
                    was_debate_beneficial=was_beneficial,
                    optimal_agent_count=optimal_count
                ))
        
        return outcomes
    
    def _generate_synthetic_data(self) -> List[DebateOutcomeRecord]:
        """Generate synthetic debate outcomes for demonstration."""
        print("Generating 1000 synthetic debate outcomes for training...")
        
        outcomes = []
        tenants = ["tenant-a", "tenant-b", "tenant-c", "demo-tenant"]
        agents = ["research", "knowledge", "strategy", "brand", "ops"]
        acceptances = ["accepted", "revised", "rejected"]
        
        for i in range(1000):
            # Vary parameters to create realistic patterns
            agent_count = np.random.choice([1, 2, 3], p=[0.4, 0.4, 0.2])
            selected_agents = np.random.choice(agents, size=agent_count, replace=False).tolist()
            tenant_id = np.random.choice(tenants)
            
            # Simulate correlation: more agents → higher cost, sometimes better quality
            base_cost = np.random.randint(100, 500)
            cost_tokens = base_cost * agent_count + np.random.randint(0, 200)
            
            base_latency = np.random.uniform(1000, 3000)  # 1-3 seconds base
            latency_ms = base_latency * agent_count + np.random.uniform(0, 1000)
            
            # Quality correlates with agent count, but with diminishing returns
            quality_boost = min(0.3, agent_count * 0.1 + np.random.uniform(-0.1, 0.1))
            acceptance_prob = 0.6 + quality_boost
            
            user_acceptance = np.random.choice(
                acceptances,
                p=[acceptance_prob, (1-acceptance_prob)*0.7, (1-acceptance_prob)*0.3]
            )
            
            evidence_count = np.random.randint(1, 10)
            citations_ok = np.random.choice([True, False], p=[0.8, 0.2])
            critique_count = max(0, agent_count - 1) + np.random.randint(0, 2)
            
            timestamp = datetime.utcnow() - timedelta(days=np.random.randint(1, 90))
            
            quality_score = self._compute_quality_score(user_acceptance, citations_ok, evidence_count)
            efficiency_score = quality_score / max(1, cost_tokens / 1000)
            was_beneficial = self._was_debate_beneficial(quality_score, agent_count, cost_tokens)
            optimal_count = self._compute_optimal_agent_count(quality_score, latency_ms, cost_tokens)
            
            outcomes.append(DebateOutcomeRecord(
                task_id=f"synthetic-{i:04d}",
                tenant_id=tenant_id,
                agents=selected_agents,
                evidence_count=evidence_count,
                citations_ok=citations_ok,
                critique_count=critique_count,
                user_acceptance=user_acceptance,
                latency_ms=latency_ms,
                cost_tokens=cost_tokens,
                timestamp=timestamp,
                quality_score=quality_score,
                efficiency_score=efficiency_score,
                was_debate_beneficial=was_beneficial,
                optimal_agent_count=optimal_count
            ))
        
        return outcomes
    
    def _compute_quality_score(self, acceptance: str, citations_ok: bool, evidence_count: int) -> float:
        """Compute quality score from outcome metrics."""
        base_score = {"accepted": 0.9, "revised": 0.6, "rejected": 0.2}[acceptance]
        citation_bonus = 0.1 if citations_ok else 0.0
        evidence_bonus = min(0.1, evidence_count * 0.01)
        return min(1.0, base_score + citation_bonus + evidence_bonus)
    
    def _was_debate_beneficial(self, quality_score: float, agent_count: int, cost_tokens: int) -> bool:
        """Determine if debate was beneficial vs single agent."""
        if agent_count == 1:
            return False  # Single agent by definition
        
        # Beneficial if high quality and reasonable cost
        efficiency = quality_score / max(1, cost_tokens / 1000)
        return quality_score > 0.7 and efficiency > 0.5
    
    def _compute_optimal_agent_count(self, quality_score: float, latency_ms: float, cost_tokens: int) -> int:
        """Compute optimal agent count based on outcome."""
        if quality_score < 0.4:
            return 1  # Single agent sufficient for low-quality needs
        elif quality_score > 0.8 and latency_ms < 5000 and cost_tokens < 1000:
            return 3  # High quality achieved efficiently
        else:
            return 2  # Balanced approach
    
    def extract_features(self, outcomes: List[DebateOutcomeRecord]) -> Tuple[np.ndarray, np.ndarray]:
        """Extract feature matrix and labels from outcomes."""
        features = []
        labels = []
        
        # Build tenant statistics for historical features
        tenant_stats = self._compute_tenant_stats(outcomes)
        
        for outcome in outcomes:
            tenant_stat = tenant_stats.get(outcome.tenant_id, {
                "avg_acceptance": 0.6,
                "avg_latency": 3000,
                "avg_quality": 0.7
            })
            
            feature_vector = [
                len(outcome.agents),  # Agent count
                outcome.evidence_count,
                1.0 if outcome.citations_ok else 0.0,
                outcome.critique_count,
                outcome.latency_ms / 1000,  # Convert to seconds
                outcome.cost_tokens / 1000,  # Scale down
                tenant_stat["avg_acceptance"],
                tenant_stat["avg_latency"] / 1000,
                tenant_stat["avg_quality"],
                # Domain-specific features (simplified)
                1.0 if "research" in outcome.agents else 0.0,
                1.0 if "strategy" in outcome.agents else 0.0,
                1.0 if "brand" in outcome.agents else 0.0,
            ]
            
            features.append(feature_vector)
            
            # Multi-class label: 0=single, 1=two-agent, 2=multi-agent
            if outcome.optimal_agent_count == 1:
                labels.append(0)
            elif outcome.optimal_agent_count == 2:
                labels.append(1)
            else:
                labels.append(2)
        
        return np.array(features), np.array(labels)
    
    def _compute_tenant_stats(self, outcomes: List[DebateOutcomeRecord]) -> Dict[str, Dict[str, float]]:
        """Compute historical statistics per tenant."""
        tenant_data = {}
        
        for outcome in outcomes:
            tenant_id = outcome.tenant_id
            if tenant_id not in tenant_data:
                tenant_data[tenant_id] = {
                    "acceptances": [],
                    "latencies": [],
                    "qualities": []
                }
            
            tenant_data[tenant_id]["acceptances"].append(
                1.0 if outcome.user_acceptance == "accepted" else 0.0
            )
            tenant_data[tenant_id]["latencies"].append(outcome.latency_ms)
            tenant_data[tenant_id]["qualities"].append(outcome.quality_score)
        
        # Compute averages
        tenant_stats = {}
        for tenant_id, data in tenant_data.items():
            tenant_stats[tenant_id] = {
                "avg_acceptance": np.mean(data["acceptances"]),
                "avg_latency": np.mean(data["latencies"]),
                "avg_quality": np.mean(data["qualities"])
            }
        
        return tenant_stats
    
    def train(self) -> Dict[str, float]:
        """Train the debate policy model."""
        print("Loading debate outcomes...")
        outcomes = self.load_debate_outcomes()
        print(f"Loaded {len(outcomes)} debate outcomes")
        
        if len(outcomes) < 50:
            print("Warning: Very few outcomes available. Model may not be reliable.")
        
        print("Extracting features...")
        X, y = self.extract_features(outcomes)
        print(f"Feature matrix shape: {X.shape}")
        print(f"Label distribution: {np.bincount(y)}")
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Scale features
        print("Scaling features...")
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Train model
        print("Training debate policy classifier...")
        self.classifier.fit(X_train_scaled, y_train)
        
        # Evaluate
        y_pred = self.classifier.predict(X_test_scaled)
        accuracy = accuracy_score(y_test, y_pred)
        
        print(f"Test accuracy: {accuracy:.3f}")
        print("\nClassification Report:")
        print(classification_report(y_test, y_pred, 
                                  target_names=["Single Agent", "Two Agents", "Multi Agent"]))
        
        # Cross-validation
        cv_scores = cross_val_score(self.classifier, X_train_scaled, y_train, cv=5)
        print(f"Cross-validation accuracy: {cv_scores.mean():.3f} (+/- {cv_scores.std() * 2:.3f})")
        
        # Feature importance
        feature_names = [
            "agent_count", "evidence_count", "citations_ok", "critique_count",
            "latency_sec", "cost_1k_tokens", "tenant_avg_acceptance", 
            "tenant_avg_latency_sec", "tenant_avg_quality",
            "has_research", "has_strategy", "has_brand"
        ]
        
        feature_importance = list(zip(feature_names, self.classifier.feature_importances_))
        feature_importance.sort(key=lambda x: x[1], reverse=True)
        
        print("\nTop 5 Most Important Features:")
        for name, importance in feature_importance[:5]:
            print(f"  {name}: {importance:.3f}")
        
        # Save model and scaler
        print(f"Saving model to {self.model_path}")
        with open(self.model_path, 'wb') as f:
            pickle.dump(self.classifier, f)
        
        print(f"Saving scaler to {self.scaler_path}")
        with open(self.scaler_path, 'wb') as f:
            pickle.dump(self.scaler, f)
        
        return {
            "accuracy": accuracy,
            "cv_mean": cv_scores.mean(),
            "cv_std": cv_scores.std(),
            "n_samples": len(outcomes),
            "n_features": X.shape[1]
        }
    
    def predict(self, features: DebateFeatures) -> Dict[str, Any]:
        """Make a prediction for a new debate request."""
        if not self.model_path.exists():
            raise FileNotFoundError(f"Model not found at {self.model_path}. Run train() first.")
        
        # Load model and scaler
        with open(self.model_path, 'rb') as f:
            classifier = pickle.load(f)
        
        with open(self.scaler_path, 'rb') as f:
            scaler = pickle.load(f)
        
        # Convert features to vector (simplified for demo)
        feature_vector = np.array([[
            len(features.preferred_agents),
            features.entity_count,
            1.0 if features.domain in ["research", "analysis"] else 0.0,
            3,  # Default critique count
            features.tenant_avg_debate_latency / 1000,
            500 / 1000,  # Default cost estimate
            features.tenant_avg_acceptance_rate,
            features.tenant_avg_debate_latency / 1000,
            features.tenant_avg_single_agent_quality,
            1.0 if "research" in features.preferred_agents else 0.0,
            1.0 if "strategy" in features.preferred_agents else 0.0,
            1.0 if "brand" in features.preferred_agents else 0.0,
        ]])
        
        # Scale and predict
        feature_vector_scaled = scaler.transform(feature_vector)
        prediction = classifier.predict(feature_vector_scaled)[0]
        probabilities = classifier.predict_proba(feature_vector_scaled)[0]
        
        # Convert prediction to recommendations
        should_single_agent = prediction == 0
        should_skip_debate = should_single_agent and probabilities[0] > 0.8
        recommended_agents = [1, 2, 3][prediction]
        confidence = probabilities[prediction]
        
        reasoning_map = {
            0: "Single agent sufficient based on historical patterns",
            1: "Two-agent debate recommended for quality vs efficiency balance",
            2: "Multi-agent debate recommended for complex task"
        }
        
        return {
            "should_single_agent": should_single_agent,
            "should_skip_debate": should_skip_debate,
            "recommended_agents": recommended_agents,
            "confidence": confidence,
            "reasoning": reasoning_map[prediction],
            "probabilities": {
                "single": probabilities[0],
                "two_agent": probabilities[1],
                "multi_agent": probabilities[2]
            }
        }


def main():
    """Main training script."""
    print("StratMaster Debate Policy Trainer - Sprint 2")
    print("=" * 50)
    
    trainer = DebatePolicyTrainer()
    
    try:
        results = trainer.train()
        print("\nTraining completed successfully!")
        print(f"Final accuracy: {results['accuracy']:.3f}")
        print(f"Model saved to: {trainer.model_path}")
        
        # Test prediction with sample features
        print("\nTesting prediction with sample features...")
        sample_features = DebateFeatures(
            query_length=50,
            estimated_complexity=0.7,
            entity_count=3,
            domain="strategy",
            tenant_avg_acceptance_rate=0.75,
            tenant_avg_debate_latency=2500,
            tenant_avg_single_agent_quality=0.65,
            preferred_agents=["strategy", "research"],
            agent_compatibility_score=0.8,
            time_pressure=False,
            quality_threshold=0.8
        )
        
        prediction = trainer.predict(sample_features)
        print(f"Sample prediction: {prediction}")
        
    except Exception as e:
        print(f"Training failed: {e}")
        raise


if __name__ == "__main__":
    main()