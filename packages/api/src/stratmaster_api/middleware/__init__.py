"""StratMaster API middleware package.

This module avoids importing heavy optional dependencies at import time.
Import specific submodules where needed.
"""

__all__: list[str] = [
	"OIDCAuthMiddleware",
	"setup_auth_middleware",
]


def __getattr__(name: str):  # pragma: no cover - simple re-export helper
	if name in {"OIDCAuthMiddleware", "setup_auth_middleware"}:
		from .auth import OIDCAuthMiddleware, setup_auth_middleware

		return {  # type: ignore[return-value]
			"OIDCAuthMiddleware": OIDCAuthMiddleware,
			"setup_auth_middleware": setup_auth_middleware,
		}[name]
	raise AttributeError(name)