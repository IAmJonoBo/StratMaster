"""Authentication middleware for StratMaster API.

Integrates Keycloak OIDC authentication with FastAPI middleware
to provide seamless authentication across all endpoints.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import HTTPException, Request, Response, status
from fastapi.security import HTTPBearer
from starlette.middleware.base import BaseHTTPMiddleware

from ..security.keycloak_auth import KeycloakAuth, OIDCConfig, get_auth

logger = logging.getLogger(__name__)


class OIDCAuthMiddleware(BaseHTTPMiddleware):
    """OIDC Authentication Middleware for FastAPI.
    
    Automatically validates JWT tokens on protected endpoints and
    injects user information into request state.
    """
    
    def __init__(self, app, auth_config: OIDCConfig | None = None):
        super().__init__(app)
        self.auth_config = auth_config
        self.auth_instance = None
        
        # Public endpoints that don't require authentication
        self.public_paths = {
            "/docs",
            "/redoc", 
            "/openapi.json",
            "/healthz",
            "/security/oidc/login",
            "/security/oidc/callback",
            "/ui/config",  # UI configuration endpoint
        }
        
        # Paths that support optional authentication
        self.optional_auth_paths = {
            "/retrieval/",
            "/research/",
        }
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request with optional OIDC authentication."""
        
        # Skip authentication for public paths
        if self._is_public_path(request.url.path):
            return await call_next(request)
        
        # Initialize auth if configured
        if self.auth_config and not self.auth_instance:
            try:
                from ..security.keycloak_auth import init_auth
                self.auth_instance = init_auth(self.auth_config)
                logger.info("OIDC authentication middleware initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize OIDC auth: {e}")
                # Continue without auth for development
                return await call_next(request)
        
        # Extract token from Authorization header
        token = self._extract_token(request)
        
        if token:
            try:
                # Validate token and get user info
                if self.auth_instance:
                    user_info = await self.auth_instance.verify_token(token)
                    request.state.user = user_info
                    request.state.authenticated = True
                    logger.debug(f"Authenticated user: {user_info.preferred_username}")
                else:
                    # Mock user for development when auth not configured
                    request.state.user = self._create_mock_user()
                    request.state.authenticated = True
                    
            except HTTPException as e:
                # Token validation failed
                if self._requires_auth(request.url.path):
                    logger.warning(f"Authentication failed for {request.url.path}: {e.detail}")
                    return Response(
                        content=f'{{"detail": "{e.detail}"}}',
                        status_code=e.status_code,
                        headers={"Content-Type": "application/json"}
                    )
                else:
                    # Optional auth - continue as anonymous
                    request.state.user = None
                    request.state.authenticated = False
        else:
            # No token provided
            if self._requires_auth(request.url.path):
                logger.warning(f"Missing authentication for protected endpoint: {request.url.path}")
                return Response(
                    content='{"detail": "Authentication required"}',
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    headers={
                        "Content-Type": "application/json",
                        "WWW-Authenticate": "Bearer"
                    }
                )
            else:
                # Optional auth - continue as anonymous  
                request.state.user = None
                request.state.authenticated = False
        
        # Continue to next middleware/endpoint
        response = await call_next(request)
        
        # Add authentication headers to response
        if hasattr(request.state, 'user') and request.state.user:
            response.headers["X-User-ID"] = request.state.user.sub
            response.headers["X-Tenant-ID"] = getattr(request.state.user, 'tenant_id', 'default')
        
        return response
    
    def _is_public_path(self, path: str) -> bool:
        """Check if path is public (no auth required)."""
        return any(path.startswith(public) for public in self.public_paths)
    
    def _requires_auth(self, path: str) -> bool:
        """Check if path requires mandatory authentication."""
        # Strategy and security endpoints require auth
        protected_prefixes = ["/debate/", "/export/", "/security/users/"]
        return any(path.startswith(prefix) for prefix in protected_prefixes)
    
    def _extract_token(self, request: Request) -> str | None:
        """Extract JWT token from Authorization header."""
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            return auth_header[7:]  # Remove 'Bearer ' prefix
        return None
    
    def _create_mock_user(self) -> Any:
        """Create mock user for development when auth is not configured."""
        from types import SimpleNamespace
        return SimpleNamespace(
            sub="dev-user-123",
            preferred_username="developer", 
            email="dev@stratmaster.local",
            roles=["analyst", "strategist"],
            permissions=["read:all", "write:own"],
            tenant_id="dev-tenant"
        )


def setup_auth_middleware(app, config: dict[str, Any] | None = None):
    """Setup authentication middleware with configuration.
    
    Args:
        app: FastAPI application instance
        config: Optional OIDC configuration dictionary
    """
    if config and config.get("enabled", False):
        auth_config = OIDCConfig(
            server_url=config["server_url"],
            realm_name=config["realm_name"], 
            client_id=config["client_id"],
            client_secret=config.get("client_secret"),
            verify_ssl=config.get("verify_ssl", True)
        )
        
        app.add_middleware(OIDCAuthMiddleware, auth_config=auth_config)
        logger.info("OIDC authentication middleware enabled")
    else:
        # Development mode - add middleware without OIDC config
        app.add_middleware(OIDCAuthMiddleware, auth_config=None)
        logger.info("Development authentication middleware enabled")


# Dependency for getting current user from middleware
async def get_current_user_from_middleware(request: Request):
    """FastAPI dependency to get current user from middleware."""
    if hasattr(request.state, 'user') and request.state.user:
        return request.state.user
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required"
    )


# Dependency for optional user (returns None if not authenticated)
async def get_optional_user_from_middleware(request: Request):
    """FastAPI dependency to get optional current user from middleware."""
    return getattr(request.state, 'user', None)