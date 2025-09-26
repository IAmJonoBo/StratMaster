"""Keycloak OIDC authentication and authorization."""

from __future__ import annotations

import asyncio
import datetime as dt
import importlib
import importlib.util as _import_util
import logging
from typing import Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field

# Detect availability without importing at module import time
KEYCLOAK_AVAILABLE: bool = _import_util.find_spec("keycloak") is not None

logger = logging.getLogger(__name__)

# Bearer token scheme for FastAPI
security = HTTPBearer()


class OIDCConfig(BaseModel):
    """OIDC configuration for Keycloak integration."""

    server_url: str = Field(..., description="Keycloak server URL")
    realm_name: str = Field(..., description="Keycloak realm name")
    client_id: str = Field(..., description="Client ID")
    client_secret: str | None = Field(None, description="Client secret (for confidential clients)")
    verify_ssl: bool = Field(True, description="Verify SSL certificates")

    # Token validation settings
    verify_signature: bool = Field(True, description="Verify JWT signature")
    verify_aud: bool = Field(True, description="Verify audience claim")
    verify_exp: bool = Field(True, description="Verify expiration claim")
    leeway: int = Field(30, description="JWT clock skew leeway in seconds")


class UserInfo(BaseModel):
    """User information from OIDC token."""

    sub: str = Field(..., description="Subject identifier")
    preferred_username: str = Field(..., description="Preferred username")
    email: str | None = Field(None, description="Email address")
    name: str | None = Field(None, description="Full name")
    given_name: str | None = Field(None, description="Given name")
    family_name: str | None = Field(None, description="Family name")

    # Authorization
    roles: list[str] = Field(default_factory=list, description="Assigned roles")
    groups: list[str] = Field(default_factory=list, description="Group memberships")
    permissions: list[str] = Field(default_factory=list, description="Specific permissions")

    # Metadata
    iat: int | None = Field(None, description="Issued at timestamp")
    exp: int | None = Field(None, description="Expiration timestamp")
    tenant_id: str | None = Field(None, description="Tenant identifier")


class KeycloakAuth:
    """Keycloak OIDC authentication and authorization manager."""

    def __init__(self, config: OIDCConfig):
        self.config = config
        if not KEYCLOAK_AVAILABLE:
            raise RuntimeError(
                "python-keycloak not installed; cannot initialize KeycloakAuth"
            )
        # Lazy import to keep dependency optional and avoid static analysis issues
        keycloak_mod = importlib.import_module("keycloak")
        self.keycloak_openid = keycloak_mod.KeycloakOpenID(
            server_url=config.server_url,
            client_id=config.client_id,
            realm_name=config.realm_name,
            client_secret_key=config.client_secret,
            verify=config.verify_ssl,
        )

        # Cache for public keys (avoid fetching on every request)
        self._public_key_cache: str | None = None
        self._cache_expires: dt.datetime | None = None

    def get_public_key(self) -> str:
        """Get Keycloak public key for JWT verification."""
        now = dt.datetime.now(dt.UTC)

        # Use cached key if available and not expired
        if (self._public_key_cache and
            self._cache_expires and
            now < self._cache_expires):
            return self._public_key_cache

        try:
            # Get public key from Keycloak
            public_key = self.keycloak_openid.public_key()  # type: ignore[attr-defined]

            # Format as PEM
            pem_key = f"-----BEGIN PUBLIC KEY-----\n{public_key}\n-----END PUBLIC KEY-----"

            # Cache for 1 hour
            self._public_key_cache = pem_key
            self._cache_expires = now + dt.timedelta(hours=1)

            logger.debug("Retrieved and cached Keycloak public key")
            return pem_key

        except Exception as e:
            logger.error("Failed to retrieve Keycloak public key: %s", e)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Authentication service unavailable",
            ) from e

    async def verify_token(self, token: str) -> UserInfo:
        """Verify and decode JWT token."""
        try:
            # Import PyJWT lazily to avoid hard dependency at import time
            import jwt  # type: ignore[import-not-found]

            # Get public key for verification
            public_key = await asyncio.to_thread(self.get_public_key)

            # Configure JWT options
            options = {
                "verify_signature": self.config.verify_signature,
                "verify_aud": self.config.verify_aud,
                "verify_exp": self.config.verify_exp,
                "require_exp": True,
                "require_iat": True,
            }

            # Decode and verify token
            payload = jwt.decode(
                token,
                public_key,
                algorithms=["RS256"],
                options=options,
                audience=self.config.client_id if self.config.verify_aud else None,
                leeway=self.config.leeway
            )

            # Extract user information
            user_info = self._extract_user_info(payload)

            logger.debug(
                "Successfully verified token for user: %s",
                user_info.preferred_username,
            )
            return user_info

        except jwt.ExpiredSignatureError as e:  # type: ignore[name-defined]
            logger.warning("Token has expired")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            ) from e
        except jwt.InvalidTokenError as e:  # type: ignore[name-defined]
            logger.warning("Invalid token: %s", e)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"},
            ) from e
        except ModuleNotFoundError as e:
            # This handles cases where PyJWT is not installed
            logger.error("Authentication service unavailable: %s", e)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Authentication service unavailable",
            ) from e
        except Exception as e:
            logger.error("Token verification failed: %s", e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Token verification failed",
            ) from e

    def _extract_user_info(self, payload: dict[str, Any]) -> UserInfo:
        """Extract user information from JWT payload."""

        # Basic user info
        user_info = UserInfo(
            sub=payload["sub"],
            preferred_username=payload.get("preferred_username", payload["sub"]),
            email=payload.get("email"),
            name=payload.get("name"),
            given_name=payload.get("given_name"),
            family_name=payload.get("family_name"),
            iat=payload.get("iat"),
            exp=payload.get("exp"),
            tenant_id=payload.get("tenant_id"),
        )

        # Extract roles (from realm_access and resource_access)
        roles = set()

        # Realm roles
        if "realm_access" in payload:
            realm_roles = payload["realm_access"].get("roles", [])
            roles.update(realm_roles)

        # Client roles
        if "resource_access" in payload:
            client_access = payload["resource_access"].get(self.config.client_id, {})
            client_roles = client_access.get("roles", [])
            roles.update(client_roles)

        user_info.roles = list(roles)

        # Extract groups
        if "groups" in payload:
            user_info.groups = payload["groups"]

        # Extract custom claims
        if "tenant_id" in payload:
            user_info.tenant_id = payload["tenant_id"]

        # Map roles to permissions (simplified)
        user_info.permissions = self._map_roles_to_permissions(user_info.roles)

        return user_info

    def _map_roles_to_permissions(self, roles: list[str]) -> list[str]:
        """Map roles to specific permissions."""
        READ_ALL = "read:all"
        WRITE_ALL = "write:all"
        DELETE_ALL = "delete:all"
        MANAGE_USERS = "manage:users"
        MANAGE_TENANTS = "manage:tenants"
        VIEW_AUDIT_LOGS = "view:audit_logs"
        permission_mapping = {
            "admin": [
                READ_ALL,
                WRITE_ALL,
                DELETE_ALL,
                MANAGE_USERS,
                MANAGE_TENANTS,
                VIEW_AUDIT_LOGS,
            ],
            "manager": [
                READ_ALL,
                "write:own",
                "create:projects",
                "manage:team",
            ],
            "analyst": [
                "read:assigned",
                "write:own",
                "create:analysis",
                "run:research",
            ],
            "viewer": [
                "read:public",
                "view:dashboards",
            ],
            "api_client": [
                "api:read",
                "api:write",
            ]
        }

        permissions = set()
        for role in roles:
            role_permissions = permission_mapping.get(role, [])
            permissions.update(role_permissions)

        return list(permissions)

    async def get_current_user(
        self,
        credentials: HTTPAuthorizationCredentials = Depends(security)
    ) -> UserInfo:
        """FastAPI dependency to get current authenticated user."""
        return await self.verify_token(credentials.credentials)

    def require_permission(self, required_permission: str):
        """Decorator/dependency to require specific permission."""

        def permission_checker(
            current_user: UserInfo = Depends(self.get_current_user)
        ) -> UserInfo:
            if required_permission not in current_user.permissions:
                logger.warning(
                    "User %s lacks permission: %s",
                    current_user.preferred_username,
                    required_permission,
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Missing required permission: {required_permission}"
                )
            return current_user

        return permission_checker

    def require_role(self, required_role: str):
        """Decorator/dependency to require specific role."""

        def role_checker(
            current_user: UserInfo = Depends(self.get_current_user)
        ) -> UserInfo:
            if required_role not in current_user.roles:
                logger.warning(
                    "User %s lacks role: %s",
                    current_user.preferred_username,
                    required_role,
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Missing required role: {required_role}"
                )
            return current_user

        return role_checker

    async def optional_auth(
        self,
        credentials: HTTPAuthorizationCredentials | None = Depends(
            HTTPBearer(auto_error=False)
        ),
    ) -> UserInfo | None:
        """Optional authentication dependency."""
        if credentials:
            try:
                return await self.verify_token(credentials.credentials)
            except HTTPException:
                return None
        return None


class RoleBasedAccessControl:
    """Role-based access control utilities."""

    def __init__(self, keycloak_auth: KeycloakAuth):
        self.auth = keycloak_auth

    def check_tenant_access(self, user: UserInfo, tenant_id: str) -> bool:
        """Check if user has access to specific tenant."""

        # Super admin has access to all tenants
        if "admin" in user.roles:
            return True

        # Check if user's tenant matches
        if user.tenant_id == tenant_id:
            return True

        # Check for cross-tenant permissions
        if f"tenant:{tenant_id}" in user.permissions:
            return True

        return False

    def check_resource_access(
        self,
        user: UserInfo,
        resource_type: str,
        action: str,
        resource_owner: str | None = None,
        tenant_id: str | None = None
    ) -> bool:
        """Check if user can perform action on resource type."""

        # Check specific permission
        permission = f"{action}:{resource_type}"
        if permission in user.permissions:
            return True

        # Check wildcard permissions
        wildcard_permission = f"{action}:all"
        if wildcard_permission in user.permissions:
            return True

        # Check ownership for own resources
        if resource_owner and resource_owner == user.sub:
            own_permission = f"{action}:own"
            if own_permission in user.permissions:
                return True

        # Check tenant access
        if tenant_id and not self.check_tenant_access(user, tenant_id):
            return False

        return False

    def filter_by_access(
        self,
        user: UserInfo,
        resources: list[dict[str, Any]],
        resource_type: str,
        action: str = "read",
        owner_field: str = "owner",
        tenant_field: str = "tenant_id"
    ) -> list[dict[str, Any]]:
        """Filter list of resources by user access permissions."""

        accessible_resources = []

        for resource in resources:
            resource_owner = resource.get(owner_field)
            resource_tenant = resource.get(tenant_field)

            if self.check_resource_access(
                user, resource_type, action, resource_owner, resource_tenant
            ):
                accessible_resources.append(resource)

        return accessible_resources


# Global instance for dependency injection
_keycloak_auth: KeycloakAuth | None = None
_rbac: RoleBasedAccessControl | None = None


def init_auth(config: OIDCConfig) -> KeycloakAuth:
    """Initialize global authentication instance."""
    global _keycloak_auth, _rbac

    # Only initialize when Keycloak client library is available
    if not KEYCLOAK_AVAILABLE:
        raise RuntimeError("Keycloak library not available; cannot init auth")
    _keycloak_auth = KeycloakAuth(config)
    _rbac = RoleBasedAccessControl(_keycloak_auth)

    logger.info(f"Initialized Keycloak authentication for realm: {config.realm_name}")
    return _keycloak_auth


def get_auth() -> KeycloakAuth:
    """Get global authentication instance."""
    if _keycloak_auth is None:
        raise RuntimeError("Authentication not initialized. Call init_auth() first.")
    return _keycloak_auth


def get_rbac() -> RoleBasedAccessControl:
    """Get global RBAC instance."""
    if _rbac is None:
        raise RuntimeError("RBAC not initialized. Call init_auth() first.")
    return _rbac


# Convenience dependencies for FastAPI
async def get_current_user() -> UserInfo:
    """FastAPI dependency to get current authenticated user."""
    auth = get_auth()
    return await auth.get_current_user()


def require_admin():
    """FastAPI dependency to require admin role."""
    auth = get_auth()
    return auth.require_role("admin")


def require_manager():
    """FastAPI dependency to require manager role."""
    auth = get_auth()
    return auth.require_role("manager")


def require_read_permission():
    """FastAPI dependency to require read permission."""
    auth = get_auth()
    return auth.require_permission("read:all")


def require_write_permission():
    """FastAPI dependency to require write permission."""
    auth = get_auth()
    return auth.require_permission("write:all")
