"""
Mobile API Router for StratMaster

Consolidated mobile API endpoints integrated into main API as part of
Sprint 1 package consolidation (ADR-001).

Original package: packages/mobile-api/
Consolidated into: packages/api/src/stratmaster_api/mobile/
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List

from .approval_workflows import (
    ApprovalItem,
    ApprovalRequest,
    ApprovalResponse,
    NotificationRequest,
    workflow_manager,
    notification_manager,
    get_current_user
)

# Create mobile router
mobile_router = APIRouter(
    prefix="/api/mobile",
    tags=["mobile"],
    dependencies=[],
    responses={404: {"description": "Not found"}},
)

@mobile_router.get("/approvals/pending", response_model=List[ApprovalItem])
async def get_pending_approvals(
    limit: int = 50,
    offset: int = 0,
    current_user=Depends(get_current_user)
):
    """Get pending approvals for the authenticated user."""
    if not workflow_manager:
        raise HTTPException(
            status_code=503,
            detail="Mobile API not initialized"
        )
    
    return await workflow_manager.get_pending_approvals(
        current_user["user_id"],
        current_user["tenant_id"],
        limit,
        offset
    )

@mobile_router.post("/approvals/{approval_id}/approve", response_model=ApprovalResponse)
async def approve_item(
    approval_id: str,
    request: ApprovalRequest,
    current_user=Depends(get_current_user)
):
    """Approve an approval item."""
    if not workflow_manager:
        raise HTTPException(
            status_code=503,
            detail="Mobile API not initialized"
        )
    
    return await workflow_manager.process_approval(
        approval_id,
        current_user["user_id"],
        "approve",
        request.comment,
        request.signature
    )

@mobile_router.post("/approvals/{approval_id}/reject", response_model=ApprovalResponse)  
async def reject_item(
    approval_id: str,
    request: ApprovalRequest,
    current_user=Depends(get_current_user)
):
    """Reject an approval item."""
    if not workflow_manager:
        raise HTTPException(
            status_code=503,
            detail="Mobile API not initialized"
        )
    
    return await workflow_manager.process_approval(
        approval_id,
        current_user["user_id"],
        "reject", 
        request.comment,
        request.signature
    )

@mobile_router.post("/notifications/register")
async def register_device(
    request: NotificationRequest,
    current_user=Depends(get_current_user)
):
    """Register device for push notifications."""
    await notification_manager.register_device(
        current_user["user_id"],
        request.device_token,
        request.platform
    )
    
    return {"success": True, "message": "Device registered successfully"}

@mobile_router.get("/health")
async def mobile_health():
    """Mobile API health check."""
    return {
        "status": "ok",
        "service": "mobile-api",
        "consolidated": True,
        "consolidation_sprint": "Sprint 1",
        "adr": "ADR-001"
    }

# Export for integration with main app
__all__ = ['mobile_router']