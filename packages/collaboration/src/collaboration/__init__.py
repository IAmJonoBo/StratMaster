"""
Real-Time Collaboration Package for StratMaster

This package provides WebSocket-based real-time collaboration features
including CRDT document synchronization and user presence management.
"""

__version__ = "0.1.0"

from .service import CollaborationService
from .models import DocumentUpdate, UserPresence, CollaborationSession

__all__ = [
    "CollaborationService", 
    "DocumentUpdate", 
    "UserPresence", 
    "CollaborationSession"
]