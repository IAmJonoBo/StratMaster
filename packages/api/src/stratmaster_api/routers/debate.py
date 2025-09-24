"""
Sprint 3 - Human-in-the-Loop Debate Endpoints

This module implements endpoints for human intervention in debates:
- POST /debate/escalate - Escalate to domain specialist
- POST /debate/accept - Accept debate outcome with notes
- GET /debate/{debate_id}/status - Get current debate status
- POST /debate/{debate_id}/pause - Pause for human input
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from ..dependencies import require_idempotency_key
from ..tracing import tracing_manager

router = APIRouter(prefix="/debate", tags=["debate"])


# Request/Response Models for Sprint 3
class DebateEscalateRequest(BaseModel):
    """Request to escalate debate to domain specialist."""
    debate_id: str
    tenant_id: str
    escalation_reason: str = Field(description="Reason for escalation")
    specialist_domain: str | None = Field(default=None, description="Preferred specialist domain")
    additional_context: dict[str, Any] = Field(default_factory=dict)


class DebateEscalateResponse(BaseModel):
    """Response after escalating debate."""
    escalation_id: str
    debate_id: str
    status: str = Field(description="Status after escalation")
    specialist_assigned: str | None = Field(default=None)
    estimated_response_time: int | None = Field(default=None, description="Estimated response time in minutes")


class DebateAcceptRequest(BaseModel):
    """Request to accept debate outcome."""
    debate_id: str
    tenant_id: str
    acceptance_type: str = Field(description="Type of acceptance: full, partial, conditional")
    notes: str | None = Field(default=None, description="Additional notes or modifications")
    action_items: list[str] = Field(default_factory=list, description="Extracted action items")
    quality_rating: int | None = Field(default=None, ge=1, le=5, description="Quality rating 1-5")


class DebateAcceptResponse(BaseModel):
    """Response after accepting debate."""
    acceptance_id: str
    debate_id: str
    status: str
    exported_artifacts: list[str] = Field(default_factory=list, description="Generated artifacts")
    next_steps: list[str] = Field(default_factory=list)


class DebateStatusResponse(BaseModel):
    """Current status of a debate."""
    debate_id: str
    tenant_id: str
    status: str = Field(description="Current debate status")
    participants: list[str] = Field(description="List of participating agents")
    current_turn: int = Field(description="Current turn number")
    total_turns: int = Field(description="Total planned turns")
    human_input_required: bool = Field(description="Whether human input is needed")
    pending_actions: list[str] = Field(default_factory=list)
    evidence_summary: dict[str, Any] = Field(default_factory=dict)
    last_updated: str = Field(description="ISO timestamp of last update")


class DebatePauseRequest(BaseModel):
    """Request to pause debate for human input."""
    debate_id: str
    tenant_id: str
    pause_reason: str = Field(description="Reason for pausing")
    timeout_minutes: int | None = Field(default=30, description="Timeout for human response")
    required_input_type: str = Field(description="Type of input needed: decision, clarification, approval")


class DebatePauseResponse(BaseModel):
    """Response after pausing debate."""
    pause_id: str
    debate_id: str
    status: str
    timeout_at: str = Field(description="ISO timestamp when pause times out")
    fallback_action: str = Field(description="Action to take if timeout occurs")


# Mock debate service for Sprint 3 implementation
class DebateService:
    """Service to handle debate operations with human intervention."""
    
    def __init__(self):
        # In-memory storage for demo (would use proper database in production)
        self.debates = {}
        self.escalations = {}
        self.pauses = {}
    
    def escalate_debate(self, request: DebateEscalateRequest) -> DebateEscalateResponse:
        """Escalate debate to domain specialist."""
        escalation_id = f"esc-{request.debate_id}-{len(self.escalations)}"
        
        # Determine specialist based on escalation reason and domain
        specialist_domain = request.specialist_domain or self._infer_specialist_domain(request.escalation_reason)
        specialist_assigned = f"{specialist_domain}-specialist"
        
        # Estimate response time based on domain and urgency
        estimated_time = self._estimate_response_time(specialist_domain, request.escalation_reason)
        
        escalation = {
            "escalation_id": escalation_id,
            "debate_id": request.debate_id,
            "tenant_id": request.tenant_id,
            "reason": request.escalation_reason,
            "specialist_domain": specialist_domain,
            "specialist_assigned": specialist_assigned,
            "status": "escalated",
            "created_at": "2024-01-01T00:00:00Z"  # Would use actual timestamp
        }
        
        self.escalations[escalation_id] = escalation
        
        # Update debate status
        if request.debate_id in self.debates:
            self.debates[request.debate_id]["status"] = "escalated"
            self.debates[request.debate_id]["escalation_id"] = escalation_id
        
        return DebateEscalateResponse(
            escalation_id=escalation_id,
            debate_id=request.debate_id,
            status="escalated",
            specialist_assigned=specialist_assigned,
            estimated_response_time=estimated_time
        )
    
    def accept_debate(self, request: DebateAcceptRequest) -> DebateAcceptResponse:
        """Accept debate outcome with notes."""
        acceptance_id = f"acc-{request.debate_id}-{len(self.debates)}"
        
        # Generate artifacts based on acceptance
        artifacts = self._generate_artifacts(request)
        next_steps = self._extract_next_steps(request)
        
        # Update debate status
        if request.debate_id in self.debates:
            self.debates[request.debate_id]["status"] = "accepted"
            self.debates[request.debate_id]["acceptance_id"] = acceptance_id
            self.debates[request.debate_id]["quality_rating"] = request.quality_rating
        
        return DebateAcceptResponse(
            acceptance_id=acceptance_id,
            debate_id=request.debate_id,
            status="accepted",
            exported_artifacts=artifacts,
            next_steps=next_steps
        )
    
    def get_debate_status(self, debate_id: str) -> DebateStatusResponse:
        """Get current status of a debate."""
        if debate_id not in self.debates:
            # Create mock debate for demo
            self.debates[debate_id] = {
                "debate_id": debate_id,
                "tenant_id": "demo-tenant",
                "status": "in_progress",
                "participants": ["research", "strategy"],
                "current_turn": 2,
                "total_turns": 3,
                "human_input_required": False,
                "pending_actions": [],
                "evidence_summary": {
                    "total_sources": 5,
                    "high_confidence": 3,
                    "medium_confidence": 2
                },
                "last_updated": "2024-01-01T00:00:00Z"
            }
        
        debate = self.debates[debate_id]
        
        return DebateStatusResponse(
            debate_id=debate_id,
            tenant_id=debate["tenant_id"],
            status=debate["status"],
            participants=debate["participants"],
            current_turn=debate["current_turn"],
            total_turns=debate["total_turns"],
            human_input_required=debate["human_input_required"],
            pending_actions=debate["pending_actions"],
            evidence_summary=debate["evidence_summary"],
            last_updated=debate["last_updated"]
        )
    
    def pause_debate(self, request: DebatePauseRequest) -> DebatePauseResponse:
        """Pause debate for human input."""
        pause_id = f"pause-{request.debate_id}-{len(self.pauses)}"
        
        # Calculate timeout
        from datetime import datetime, timedelta
        timeout_at = datetime.utcnow() + timedelta(minutes=request.timeout_minutes or 30)
        
        # Determine fallback action
        fallback_action = self._determine_fallback_action(request.required_input_type)
        
        pause = {
            "pause_id": pause_id,
            "debate_id": request.debate_id,
            "tenant_id": request.tenant_id,
            "reason": request.pause_reason,
            "required_input_type": request.required_input_type,
            "status": "paused",
            "timeout_at": timeout_at.isoformat(),
            "fallback_action": fallback_action
        }
        
        self.pauses[pause_id] = pause
        
        # Update debate status
        if request.debate_id in self.debates:
            self.debates[request.debate_id]["status"] = "paused"
            self.debates[request.debate_id]["human_input_required"] = True
            self.debates[request.debate_id]["pause_id"] = pause_id
        
        return DebatePauseResponse(
            pause_id=pause_id,
            debate_id=request.debate_id,
            status="paused",
            timeout_at=timeout_at.isoformat(),
            fallback_action=fallback_action
        )
    
    def _infer_specialist_domain(self, escalation_reason: str) -> str:
        """Infer specialist domain from escalation reason."""
        reason_lower = escalation_reason.lower()
        
        if any(word in reason_lower for word in ["brand", "marketing", "customer", "messaging"]):
            return "brand"
        elif any(word in reason_lower for word in ["strategy", "business", "planning", "roadmap"]):
            return "strategy"
        elif any(word in reason_lower for word in ["research", "data", "analysis", "evidence"]):
            return "research"
        elif any(word in reason_lower for word in ["process", "ops", "workflow", "system"]):
            return "ops"
        else:
            return "knowledge"
    
    def _estimate_response_time(self, specialist_domain: str, escalation_reason: str) -> int:
        """Estimate specialist response time in minutes."""
        # Simple heuristic based on domain and urgency
        base_times = {
            "brand": 45,
            "strategy": 60,
            "research": 30,
            "ops": 20,
            "knowledge": 15
        }
        
        base_time = base_times.get(specialist_domain, 30)
        
        # Adjust for urgency indicators
        if any(word in escalation_reason.lower() for word in ["urgent", "asap", "immediate"]):
            return max(15, base_time // 2)
        elif any(word in escalation_reason.lower() for word in ["complex", "detailed", "thorough"]):
            return base_time * 2
        
        return base_time
    
    def _generate_artifacts(self, request: DebateAcceptRequest) -> list[str]:
        """Generate artifacts based on acceptance."""
        artifacts = []
        
        if request.acceptance_type == "full":
            artifacts.extend(["strategy_brief.pdf", "action_plan.xlsx"])
        elif request.acceptance_type == "partial":
            artifacts.extend(["draft_recommendations.md"])
        
        if request.action_items:
            artifacts.append("action_items.json")
        
        if request.notes:
            artifacts.append("acceptance_notes.txt")
        
        return artifacts
    
    def _extract_next_steps(self, request: DebateAcceptRequest) -> list[str]:
        """Extract next steps from acceptance."""
        next_steps = []
        
        if request.acceptance_type == "full":
            next_steps.extend([
                "Review generated strategy brief",
                "Schedule stakeholder presentation",
                "Begin implementation planning"
            ])
        elif request.acceptance_type == "partial":
            next_steps.extend([
                "Address outstanding concerns",
                "Refine recommendations",
                "Schedule follow-up review"
            ])
        elif request.acceptance_type == "conditional":
            next_steps.extend([
                "Validate conditions are met",
                "Monitor implementation metrics",
                "Schedule progress review"
            ])
        
        return next_steps
    
    def _determine_fallback_action(self, input_type: str) -> str:
        """Determine fallback action for timeout."""
        fallback_map = {
            "decision": "proceed_with_default_recommendation",
            "clarification": "proceed_with_best_interpretation",
            "approval": "escalate_to_supervisor"
        }
        
        return fallback_map.get(input_type, "pause_and_notify")


# Service instance
debate_service = DebateService()


# Endpoints
@router.post("/escalate", response_model=DebateEscalateResponse)
async def escalate_debate(
    payload: DebateEscalateRequest,
    _: str = Depends(require_idempotency_key),
) -> DebateEscalateResponse:
    """Escalate debate to domain specialist - Sprint 3 HITL."""
    with tracing_manager.trace_operation("debate:escalate", {
        "tenant_id": payload.tenant_id,
        "debate_id": payload.debate_id,
        "specialist_domain": payload.specialist_domain,
        "escalation_reason": payload.escalation_reason[:100]  # Truncate for tracing
    }) as trace_context:
        result = debate_service.escalate_debate(payload)
        return result


@router.post("/accept", response_model=DebateAcceptResponse)
async def accept_debate(
    payload: DebateAcceptRequest,
    _: str = Depends(require_idempotency_key),
) -> DebateAcceptResponse:
    """Accept debate outcome with notes - Sprint 3 HITL."""
    with tracing_manager.trace_operation("debate:accept", {
        "tenant_id": payload.tenant_id,
        "debate_id": payload.debate_id,
        "acceptance_type": payload.acceptance_type,
        "quality_rating": payload.quality_rating,
        "has_notes": bool(payload.notes),
        "action_items_count": len(payload.action_items)
    }) as trace_context:
        result = debate_service.accept_debate(payload)
        return result


@router.get("/{debate_id}/status", response_model=DebateStatusResponse)
async def get_debate_status(debate_id: str) -> DebateStatusResponse:
    """Get current status of a debate - Sprint 3 HITL."""
    with tracing_manager.trace_operation("debate:status", {
        "debate_id": debate_id
    }) as trace_context:
        result = debate_service.get_debate_status(debate_id)
        return result


@router.post("/{debate_id}/pause", response_model=DebatePauseResponse)
async def pause_debate(
    debate_id: str,
    payload: DebatePauseRequest,
    _: str = Depends(require_idempotency_key),
) -> DebatePauseResponse:
    """Pause debate for human input - Sprint 3 HITL."""
    # Ensure debate_id matches
    if payload.debate_id != debate_id:
        raise HTTPException(
            status_code=400,
            detail="Debate ID in path must match debate ID in payload"
        )
    
    with tracing_manager.trace_operation("debate:pause", {
        "tenant_id": payload.tenant_id,
        "debate_id": debate_id,
        "pause_reason": payload.pause_reason[:100],
        "required_input_type": payload.required_input_type,
        "timeout_minutes": payload.timeout_minutes
    }) as trace_context:
        result = debate_service.pause_debate(payload)
        return result