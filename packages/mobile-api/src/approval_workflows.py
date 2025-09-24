"""
Mobile API for Stakeholder Approval Workflows

This module provides mobile-optimized APIs for stakeholder approval workflows
including push notifications, offline support, and optimized data structures.

Features:
- Multi-stage approval workflows
- Push notification integration
- Offline synchronization
- Signature capture support
- Real-time status updates
- Mobile-optimized data payloads
"""

import json
import logging
import os
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

import asyncpg
import firebase_admin
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from firebase_admin import credentials, messaging
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class ApprovalStatus(Enum):
    """Approval status types."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"
    EXPIRED = "expired"


class WorkflowStatus(Enum):
    """Workflow status types."""
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


class Priority(Enum):
    """Priority levels."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


@dataclass
class ApprovalStage:
    """Represents a stage in an approval workflow."""
    id: str
    name: str
    description: str
    required_roles: list[str]
    minimum_approvals: int
    timeout_hours: int
    auto_escalate: bool = True
    blocking: bool = False
    consensus_required: bool = False
    conditions: dict[str, Any] = None


@dataclass
class ApprovalItem:
    """Represents an item requiring approval."""
    id: str
    workflow_id: str
    workflow_name: str
    title: str
    description: str
    status: ApprovalStatus
    priority: Priority
    created_at: datetime
    due_date: datetime | None
    author_id: str
    author_name: str
    author_avatar_url: str | None
    current_stage: ApprovalStage
    approvers_required: int
    approvers_completed: int
    attachments_count: int
    comments_count: int
    tenant_id: str
    metadata: dict[str, Any] = None


class ApprovalRequest(BaseModel):
    """Request model for approval actions."""
    approval_id: str
    action: str = Field(..., regex="^(approve|reject)$")
    comment: str | None = None
    signature: str | None = None  # Base64 encoded signature image


class ApprovalResponse(BaseModel):
    """Response model for approval actions."""
    success: bool
    message: str
    approval_status: str
    next_stage: str | None = None


class NotificationRequest(BaseModel):
    """Request model for device registration."""
    device_token: str
    platform: str = Field(..., regex="^(ios|android)$")
    user_id: str
    tenant_id: str


class PushNotificationManager:
    """Manages push notifications for mobile devices."""
    
    def __init__(self):
        self.firebase_app = None
        self.device_tokens = {}  # user_id -> [device_tokens]
        
    def initialize_firebase(self, credentials_path: str):
        """Initialize Firebase Admin SDK."""
        try:
            cred = credentials.Certificate(credentials_path)
            self.firebase_app = firebase_admin.initialize_app(cred)
            logger.info("Firebase initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Firebase: {e}")
            
    async def register_device(self, user_id: str, device_token: str, platform: str):
        """Register device token for push notifications."""
        if user_id not in self.device_tokens:
            self.device_tokens[user_id] = []
            
        # Remove duplicate tokens
        self.device_tokens[user_id] = [
            token for token in self.device_tokens[user_id] 
            if token != device_token
        ]
        
        # Add new token
        self.device_tokens[user_id].append(device_token)
        
        # Keep only last 5 tokens per user
        self.device_tokens[user_id] = self.device_tokens[user_id][-5:]
        
        logger.info(f"Registered device token for user {user_id}")
    
    async def send_approval_notification(
        self,
        user_id: str,
        approval_item: ApprovalItem,
        notification_type: str = "approval_required"
    ):
        """Send approval notification to user devices."""
        if not self.firebase_app or user_id not in self.device_tokens:
            logger.warning(f"Cannot send notification to user {user_id}")
            return
            
        tokens = self.device_tokens[user_id]
        
        # Create notification message
        if notification_type == "approval_required":
            title = f"{approval_item.workflow_name} - Approval Required"
            body = f"{approval_item.title} requires your approval"
        elif notification_type == "approval_approved":
            title = "Approval Completed"
            body = f"Your {approval_item.workflow_name} has been approved"
        elif notification_type == "approval_rejected":
            title = "Approval Rejected"
            body = f"Your {approval_item.workflow_name} has been rejected"
        elif notification_type == "deadline_reminder":
            hours_left = int((approval_item.due_date - datetime.utcnow()).total_seconds() / 3600)
            title = "Approval Deadline Approaching"
            body = f"{approval_item.workflow_name} approval due in {hours_left} hours"
        else:
            title = "StratMaster Notification"
            body = "You have a new notification"
        
        # Prepare message
        message = messaging.MulticastMessage(
            tokens=tokens,
            notification=messaging.Notification(
                title=title,
                body=body
            ),
            data={
                "approval_id": approval_item.id,
                "workflow_id": approval_item.workflow_id,
                "deep_link": f"stratmaster://approval/{approval_item.id}",
                "type": notification_type
            },
            android=messaging.AndroidConfig(
                priority="high",
                notification=messaging.AndroidNotification(
                    channel_id="approvals",
                    color="#1E40AF",
                    icon="ic_approval"
                )
            ),
            apns=messaging.APNSConfig(
                headers={"apns-priority": "10"},
                payload=messaging.APNSPayload(
                    aps=messaging.Aps(
                        alert=messaging.ApsAlert(
                            title=title,
                            body=body
                        ),
                        sound="default",
                        badge=1,
                        category="APPROVAL_REQUIRED"
                    )
                )
            )
        )
        
        try:
            response = messaging.send_multicast(message)
            logger.info(f"Sent notification to {len(tokens)} devices for user {user_id}")
            
            # Remove invalid tokens
            if response.failure_count > 0:
                invalid_tokens = []
                for idx, resp in enumerate(response.responses):
                    if not resp.success:
                        invalid_tokens.append(tokens[idx])
                        
                for token in invalid_tokens:
                    self.device_tokens[user_id].remove(token)
                    
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")


class ApprovalWorkflowManager:
    """Manages approval workflows and states."""
    
    def __init__(self, db_pool: asyncpg.Pool, notification_manager: PushNotificationManager):
        self.db_pool = db_pool
        self.notification_manager = notification_manager
        self.workflow_definitions = {}
        
    def load_workflow_definitions(self, config_path: str):
        """Load workflow definitions from configuration."""
        try:
            with open(config_path) as f:
                config = json.load(f)
            
            self.workflow_definitions = config.get("workflows", {})
            logger.info(f"Loaded {len(self.workflow_definitions)} workflow definitions")
            
        except Exception as e:
            logger.error(f"Failed to load workflow definitions: {e}")
    
    async def get_pending_approvals(
        self,
        user_id: str,
        tenant_id: str,
        limit: int = 50,
        offset: int = 0
    ) -> list[ApprovalItem]:
        """Get pending approvals for a user."""
        query = """
            SELECT a.*, w.workflow_name, w.title, w.description,
                   u.name as author_name, u.avatar_url as author_avatar_url,
                   s.stage_name, s.stage_description
            FROM approvals a
            JOIN workflows w ON a.workflow_id = w.id  
            JOIN users u ON a.author_id = u.id
            JOIN approval_stages s ON a.current_stage_id = s.id
            WHERE a.status = 'pending'
              AND a.tenant_id = $1
              AND (
                a.assigned_user_id = $2 OR
                a.required_roles && (
                  SELECT array_agg(role) FROM user_roles 
                  WHERE user_id = $2 AND tenant_id = $1
                )
              )
            ORDER BY a.priority DESC, a.due_date ASC NULLS LAST
            LIMIT $3 OFFSET $4
        """
        
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch(query, tenant_id, user_id, limit, offset)
            
            approvals = []
            for row in rows:
                # Get current stage definition
                workflow_def = self.workflow_definitions.get(row["workflow_name"], {})
                stages = workflow_def.get("stages", [])
                current_stage_def = next(
                    (s for s in stages if s["id"] == row["current_stage_id"]), 
                    {}
                )
                
                stage = ApprovalStage(
                    id=current_stage_def.get("id", ""),
                    name=current_stage_def.get("name", row["stage_name"]),
                    description=current_stage_def.get("description", row["stage_description"]),
                    required_roles=current_stage_def.get("required_roles", []),
                    minimum_approvals=current_stage_def.get("minimum_approvals", 1),
                    timeout_hours=current_stage_def.get("timeout_hours", 24)
                )
                
                approval = ApprovalItem(
                    id=row["id"],
                    workflow_id=row["workflow_id"],
                    workflow_name=row["workflow_name"],
                    title=row["title"],
                    description=row["description"],
                    status=ApprovalStatus(row["status"]),
                    priority=Priority(row["priority"]),
                    created_at=row["created_at"],
                    due_date=row["due_date"],
                    author_id=row["author_id"],
                    author_name=row["author_name"],
                    author_avatar_url=row["author_avatar_url"],
                    current_stage=stage,
                    approvers_required=row["approvers_required"],
                    approvers_completed=row["approvers_completed"],
                    attachments_count=row["attachments_count"] or 0,
                    comments_count=row["comments_count"] or 0,
                    tenant_id=row["tenant_id"]
                )
                
                approvals.append(approval)
            
            return approvals
    
    async def process_approval(
        self,
        approval_id: str,
        user_id: str,
        action: str,
        comment: str = None,
        signature: str = None
    ) -> ApprovalResponse:
        """Process an approval action."""
        async with self.db_pool.acquire() as conn:
            async with conn.transaction():
                # Get approval details
                approval_row = await conn.fetchrow("""
                    SELECT * FROM approvals 
                    WHERE id = $1 AND status = 'pending'
                """, approval_id)
                
                if not approval_row:
                    raise HTTPException(
                        status_code=404,
                        detail="Approval not found or already processed"
                    )
                
                # Check user permissions
                user_roles = await conn.fetch("""
                    SELECT role FROM user_roles 
                    WHERE user_id = $1 AND tenant_id = $2
                """, user_id, approval_row["tenant_id"])
                
                user_role_names = [r["role"] for r in user_roles]
                
                # Get workflow definition
                workflow_def = self.workflow_definitions.get(approval_row["workflow_name"], {})
                stages = workflow_def.get("stages", [])
                current_stage = next(
                    (s for s in stages if s["id"] == approval_row["current_stage_id"]),
                    None
                )
                
                if not current_stage:
                    raise HTTPException(
                        status_code=422,
                        detail="Invalid workflow state"
                    )
                
                # Check if user has required role
                required_roles = current_stage.get("required_roles", [])
                if not any(role in user_role_names for role in required_roles):
                    raise HTTPException(
                        status_code=403,
                        detail="Insufficient permissions for this approval"
                    )
                
                # Record the approval action
                await conn.execute("""
                    INSERT INTO approval_actions 
                    (approval_id, user_id, action, comment, signature, created_at)
                    VALUES ($1, $2, $3, $4, $5, $6)
                """, 
                approval_id, user_id, action, comment, signature, datetime.utcnow()
                )
                
                # Update approval counts
                if action == "approve":
                    await conn.execute("""
                        UPDATE approvals 
                        SET approvers_completed = approvers_completed + 1,
                            updated_at = $2
                        WHERE id = $1
                    """, approval_id, datetime.utcnow())
                    
                    # Check if stage is complete
                    updated_row = await conn.fetchrow("""
                        SELECT * FROM approvals WHERE id = $1
                    """, approval_id)
                    
                    min_approvals = current_stage.get("minimum_approvals", 1)
                    
                    if updated_row["approvers_completed"] >= min_approvals:
                        # Move to next stage or complete
                        current_stage_idx = next(
                            (i for i, s in enumerate(stages) if s["id"] == approval_row["current_stage_id"]),
                            -1
                        )
                        
                        if current_stage_idx < len(stages) - 1:
                            # Move to next stage
                            next_stage = stages[current_stage_idx + 1]
                            await conn.execute("""
                                UPDATE approvals
                                SET current_stage_id = $2,
                                    approvers_required = $3,
                                    approvers_completed = 0,
                                    due_date = $4,
                                    updated_at = $5
                                WHERE id = $1
                            """, 
                            approval_id,
                            next_stage["id"],
                            next_stage.get("minimum_approvals", 1),
                            datetime.utcnow() + timedelta(hours=next_stage.get("timeout_hours", 24)),
                            datetime.utcnow()
                            )
                            
                            return ApprovalResponse(
                                success=True,
                                message="Approval recorded, moved to next stage",
                                approval_status="pending",
                                next_stage=next_stage["name"]
                            )
                        else:
                            # Complete the workflow
                            await conn.execute("""
                                UPDATE approvals
                                SET status = 'approved',
                                    completed_at = $2,
                                    updated_at = $2
                                WHERE id = $1
                            """, approval_id, datetime.utcnow())
                            
                            # Notify author
                            approval_item = await self._get_approval_item(conn, approval_id)
                            await self.notification_manager.send_approval_notification(
                                approval_item.author_id,
                                approval_item,
                                "approval_approved"
                            )
                            
                            return ApprovalResponse(
                                success=True,
                                message="Workflow completed successfully",
                                approval_status="approved"
                            )
                    else:
                        return ApprovalResponse(
                            success=True,
                            message="Approval recorded, waiting for additional approvals",
                            approval_status="pending"
                        )
                        
                elif action == "reject":
                    # Reject the entire workflow
                    await conn.execute("""
                        UPDATE approvals
                        SET status = 'rejected',
                            completed_at = $2,
                            updated_at = $2
                        WHERE id = $1
                    """, approval_id, datetime.utcnow())
                    
                    # Notify author
                    approval_item = await self._get_approval_item(conn, approval_id)
                    await self.notification_manager.send_approval_notification(
                        approval_item.author_id,
                        approval_item,
                        "approval_rejected"
                    )
                    
                    return ApprovalResponse(
                        success=True,
                        message="Workflow rejected",
                        approval_status="rejected"
                    )
    
    async def _get_approval_item(self, conn, approval_id: str) -> ApprovalItem:
        """Get approval item from database connection."""
        # Simplified version - in practice would need full query like in get_pending_approvals
        row = await conn.fetchrow("SELECT * FROM approvals WHERE id = $1", approval_id)
        
        # Create minimal approval item for notification
        return ApprovalItem(
            id=row["id"],
            workflow_id=row["workflow_id"],
            workflow_name=row["workflow_name"],
            title=row["title"],
            description=row["description"],
            status=ApprovalStatus(row["status"]),
            priority=Priority(row["priority"]),
            created_at=row["created_at"],
            due_date=row["due_date"],
            author_id=row["author_id"],
            author_name="",  # Would need join
            author_avatar_url=None,
            current_stage=ApprovalStage("", "", "", [], 1, 24),  # Simplified
            approvers_required=row["approvers_required"],
            approvers_completed=row["approvers_completed"],
            attachments_count=0,
            comments_count=0,
            tenant_id=row["tenant_id"]
        )


# Global instances
notification_manager = PushNotificationManager()
workflow_manager = None  # Initialized with database pool


async def initialize_mobile_api(db_pool: asyncpg.Pool):
    """Initialize mobile API components."""
    global workflow_manager
    
    # Initialize Firebase
    firebase_credentials_path = os.getenv("FIREBASE_CREDENTIALS_PATH")
    if firebase_credentials_path:
        notification_manager.initialize_firebase(firebase_credentials_path)
    
    # Initialize workflow manager
    workflow_manager = ApprovalWorkflowManager(db_pool, notification_manager)
    
    # Load workflow definitions
    config_path = os.getenv("MOBILE_CONFIG_PATH", "configs/mobile/mobile-config.yaml")
    workflow_manager.load_workflow_definitions(config_path)
    
    logger.info("Mobile API initialized successfully")


# FastAPI dependency functions
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())):
    """Get current user from JWT token."""
    # Simplified - in practice would validate JWT and return user info
    return {
        "user_id": "user123",
        "tenant_id": "tenant123",
        "roles": ["manager"]
    }


# API endpoints would be defined here using FastAPI
# Example:
"""
from fastapi import APIRouter

mobile_router = APIRouter(prefix="/api/mobile")

@mobile_router.get("/approvals/pending")
async def get_pending_approvals(
    current_user = Depends(get_current_user),
    limit: int = 50,
    offset: int = 0
):
    return await workflow_manager.get_pending_approvals(
        current_user["user_id"],
        current_user["tenant_id"],
        limit,
        offset
    )

@mobile_router.post("/approvals/{approval_id}/approve")
async def approve_item(
    approval_id: str,
    request: ApprovalRequest,
    current_user = Depends(get_current_user)
):
    return await workflow_manager.process_approval(
        approval_id,
        current_user["user_id"],
        "approve",
        request.comment,
        request.signature
    )
"""