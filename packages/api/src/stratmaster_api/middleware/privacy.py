"""Privacy-aware middleware for request/response sanitisation."""

from __future__ import annotations

import json
from typing import Any

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from ..security.privacy_controls import DataSource
from ..tracing import tracing_manager


class PrivacyRedactionMiddleware(BaseHTTPMiddleware):
    """Annotate requests/responses with redacted mirrors for logging and tracing."""

    def __init__(
        self,
        app,
        privacy_manager: Any,
        *,
        default_workspace: str = "system",
        redact_requests: bool = True,
        redact_responses: bool = True,
    ) -> None:
        super().__init__(app)
        self.privacy_manager = privacy_manager
        self.default_workspace = default_workspace
        self.redact_requests = redact_requests
        self.redact_responses = redact_responses

    async def dispatch(self, request: Request, call_next) -> Response:
        workspace_id = self._resolve_workspace_id(request)
        request.state.workspace_id = workspace_id

        token = tracing_manager.push_privacy_context(workspace_id)

        if self.redact_requests:
            request_body = await self._read_body(request)
            redacted_request = self._redact_text(workspace_id, request_body, DataSource.USER_INPUT)
            request.state.privacy_request = redacted_request

        try:
            response = await call_next(request)
        finally:
            tracing_manager.reset_privacy_context(token)

        if self.redact_responses:
            response_body = self._extract_response_body(response)
            redacted_response = self._redact_text(
                workspace_id,
                response_body,
                DataSource.API_RESPONSES,
            )
            request.state.privacy_response = redacted_response

        return response

    def _resolve_workspace_id(self, request: Request) -> str:
        header_keys = ("x-workspace-id", "x-tenant-id", "x-org-id")
        for key in header_keys:
            value = request.headers.get(key)
            if value:
                return value
        return self.default_workspace

    async def _read_body(self, request: Request) -> str:
        try:
            body_bytes = await request.body()
        except RuntimeError:
            return ""

        # Restore body for downstream handlers
        request._body = body_bytes  # type: ignore[attr-defined]

        if not body_bytes:
            return ""

        content_type = request.headers.get("content-type", "")
        if "application/json" in content_type:
            try:
                parsed = json.loads(body_bytes)
                return json.dumps(parsed, separators=(",", ":"))
            except json.JSONDecodeError:
                return body_bytes.decode("utf-8", errors="ignore")
        return body_bytes.decode("utf-8", errors="ignore")

    def _extract_response_body(self, response: Response) -> str:
        body: bytes | str | None = getattr(response, "body", None)
        if body is None:
            return ""
        if isinstance(body, bytes):
            try:
                # Attempt to parse JSON to yield stable ordering for logging
                parsed = json.loads(body)
                return json.dumps(parsed, separators=(",", ":"))
            except json.JSONDecodeError:
                return body.decode("utf-8", errors="ignore")
        return str(body)

    def _redact_text(
        self,
        workspace_id: str,
        text: str,
        data_source: DataSource,
    ) -> dict[str, Any]:
        if not text or not self.privacy_manager:
            return {
                "original_text": text,
                "processed_text": text,
                "redacted": False,
                "privacy_applied": [],
            }

        process = getattr(self.privacy_manager, "process_text_for_privacy", None)
        if process is None:
            return {
                "original_text": text,
                "processed_text": text,
                "redacted": False,
                "privacy_applied": [],
            }

        try:
            result = process(
                workspace_id=workspace_id,
                text=text,
                data_source=data_source,
                language="en",
            )
        except Exception:
            return {
                "original_text": text,
                "processed_text": text,
                "redacted": False,
                "privacy_applied": [],
            }

        if not isinstance(result, dict):
            return {
                "original_text": text,
                "processed_text": text,
                "redacted": False,
                "privacy_applied": [],
            }

        result.setdefault("original_text", text)
        result.setdefault("processed_text", text)
        result.setdefault("redacted", False)
        result.setdefault("privacy_applied", [])
        return result
