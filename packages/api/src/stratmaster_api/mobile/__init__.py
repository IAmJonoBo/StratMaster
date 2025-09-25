"""
Mobile API Module for StratMaster

This module provides mobile-optimized APIs and functionality consolidated from 
the separate mobile-api package as part of Sprint 1 package consolidation.

Consolidated from: packages/mobile-api/
"""

from .approval_workflows import (
    ApprovalStatus,
    WorkflowStatus,
    Priority,
    ApprovalStage,
    ApprovalItem,
    ApprovalRequest,
    ApprovalResponse,
    NotificationRequest,
    PushNotificationManager,
    ApprovalWorkflowManager,
    initialize_mobile_api,
    get_current_user,
    notification_manager,
    workflow_manager
)

__all__ = [
    'ApprovalStatus',
    'WorkflowStatus', 
    'Priority',
    'ApprovalStage',
    'ApprovalItem',
    'ApprovalRequest',
    'ApprovalResponse',
    'NotificationRequest',
    'PushNotificationManager',
    'ApprovalWorkflowManager',
    'initialize_mobile_api',
    'get_current_user',
    'notification_manager',
    'workflow_manager'
]