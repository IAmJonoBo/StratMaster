"""Security middleware for StratMaster API."""

from __future__ import annotations

import logging
import time
from collections.abc import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class SecurityMiddleware(BaseHTTPMiddleware):
    """Security middleware for audit logging and privacy enforcement."""
    
    def __init__(self, app, audit_logger=None, privacy_manager=None):
        super().__init__(app)
        self.audit_logger = audit_logger
        self.privacy_manager = privacy_manager
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with security controls."""
        
        # Extract request information
        start_time = time.time()
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        method = request.method
        url = str(request.url)
        
        # Process request
        response = await call_next(request)
        
        # Calculate duration
        duration_ms = int((time.time() - start_time) * 1000)
        
        # Log API call if audit logger available
        if self.audit_logger:
            try:
                user_id = getattr(request.state, 'user_id', None)
                workspace_id = getattr(request.state, 'workspace_id', None)
                
                # Create a simple audit event for API calls
                self.audit_logger.log_system_event(
                    event_type="api_call",
                    action=f"{method} {url}",
                    description=f"API call to {method} {url}",
                    success=response.status_code < 400,
                    metadata={
                        "status_code": response.status_code,
                        "method": method,
                        "endpoint": url,
                        "user_id": user_id,
                        "workspace_id": workspace_id,
                        "ip_address": client_ip,
                        "user_agent": user_agent,
                        "duration_ms": duration_ms
                    }
                )
            except Exception as e:
                logger.error(f"Failed to log API call: {e}")
        
        return response