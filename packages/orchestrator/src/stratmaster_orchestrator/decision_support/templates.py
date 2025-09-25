"""Static templates used by the decision-support CLI."""

ACH_TEMPLATE = {
    "title": "Feature Launch Readiness",
    "context": "Evaluate whether the upcoming launch is ready for public release",
    "hypotheses": [
        {"id": "H1", "statement": "The feature is ready for global launch"},
        {"id": "H2", "statement": "The feature requires extended beta"},
        {"id": "H3", "statement": "The feature should be cancelled"},
    ],
    "evidence": [
        {
            "id": "E1",
            "description": "Performance tests show p95 latency under target",
            "assessments": {"H1": "support", "H2": "contradict", "H3": "contradict"},
            "weight": 1.0,
        }
    ],
    "decision": {"verdict": "undecided", "rationale": "Pending additional evidence"},
    "actions": [
        {"owner": "release@stratmaster.io", "description": "Collect canary results", "due_date": "2025-01-31"}
    ],
}

PREMORTEM_TEMPLATE = {
    "initiative": "Feature Launch Readiness",
    "time_horizon": "30 days post launch",
    "success_definition": "95% customer satisfaction and <1% incident rate",
    "catastrophe": "Critical reliability incident forces rollback",
    "risk_triggers": [
        "Spike in latency > 300ms",
        "Pager load > 3 incidents per week",
        "Negative sentiment from top 5 enterprise customers",
    ],
    "mitigations": [
        {"risk": "latency", "action": "Auto-scale to 3x capacity", "owner": "platform@stratmaster.io"}
    ],
    "confidence_score": 0.6,
}

__all__ = ["ACH_TEMPLATE", "PREMORTEM_TEMPLATE"]
