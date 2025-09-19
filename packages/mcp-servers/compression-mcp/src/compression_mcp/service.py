"""Compression service leveraging LLMLingua when available."""

from __future__ import annotations

import logging

from .config import AppConfig
from .models import CompressRequest, CompressResponse

logger = logging.getLogger(__name__)

try:  # pragma: no cover - optional dependency
    from llmlingua import PromptCompressor
except ImportError:  # pragma: no cover
    PromptCompressor = None


class CompressionService:
    def __init__(self, config: AppConfig):
        self.config = config
        self._compressor = None
        if config.provider.enable_llmlingua and PromptCompressor is not None:
            try:  # pragma: no cover - heavy dependency
                self._compressor = PromptCompressor()
            except Exception as exc:
                logger.warning(
                    "Failed to initialise LLMLingua; falling back", exc_info=exc
                )

    def compress(self, payload: CompressRequest) -> CompressResponse:
        original_tokens = len(payload.text.split())
        if self._compressor is not None:
            try:  # pragma: no cover
                result = self._compressor.compress_prompt(
                    payload.text,
                    ratio=float(payload.target_tokens) / max(original_tokens, 1),
                )
                compressed_text = result["compressed_prompt"]
                compressed_tokens = len(compressed_text.split())
                return CompressResponse(
                    compressed=compressed_text,
                    original_tokens=original_tokens,
                    compressed_tokens=compressed_tokens,
                    provider=self.config.provider.name,
                )
            except Exception as exc:
                logger.warning(
                    "LLMLingua compression failed; using heuristic fallback",
                    exc_info=exc,
                )

        compressed_text = self._fallback_compress(payload.text, payload.target_tokens)
        compressed_tokens = len(compressed_text.split())
        return CompressResponse(
            compressed=compressed_text,
            original_tokens=original_tokens,
            compressed_tokens=compressed_tokens,
            provider="synthetic",
        )

    @staticmethod
    def _fallback_compress(text: str, target_tokens: int) -> str:
        tokens = text.split()
        if len(tokens) <= target_tokens:
            return text
        return " ".join(tokens[:target_tokens]) + " ..."
