"""StratMaster API middleware package.

Avoid importing heavy optional dependencies at package import time. Import
middleware classes/functions directly from their modules when needed, e.g.:

from stratmaster_api.middleware.auth import OIDCAuthMiddleware, setup_auth_middleware
from stratmaster_api.middleware.performance_cache import ResponseCachingMiddleware
"""

__all__: list[str] = [
	# intentionally empty to avoid side effects on import
]
