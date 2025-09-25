"""Thin wrapper around HuggingFace inference used for optional critiques."""

from __future__ import annotations

import importlib.util
import os
from dataclasses import dataclass, field
from typing import Iterable, Sequence

_HF_AVAILABLE = importlib.util.find_spec("huggingface_hub") is not None
DEFAULT_MODEL = "meta-llama/Llama-3.1-8B-Instruct"

if _HF_AVAILABLE:  # pragma: no cover - optional dependency
    from huggingface_hub import InferenceClient  # type: ignore
else:  # pragma: no cover - fallback when dependency unavailable
    InferenceClient = object  # sentinel


@dataclass(slots=True)
class HuggingFaceCritiqueEngine:
    """Optional connector to HuggingFace text-generation endpoints."""

    model: str = DEFAULT_MODEL
    token: str | None = None
    max_new_tokens: int = 192
    temperature: float = 0.2
    system_prompt: str = (
        "You are a governance reviewer analysing decision records for risk, guardrails, and "
        "ethical compliance. Provide concise bullets prioritising the highest-impact concerns."
    )
    _client: InferenceClient | None = field(init=False, default=None, repr=False)

    def __post_init__(self) -> None:
        if not _HF_AVAILABLE:
            return
        try:
            self._client = InferenceClient(model=self.model, token=self.token or os.getenv("HUGGINGFACE_API_TOKEN"))
        except Exception:  # pragma: no cover - defensive fallback
            self._client = None

    @property
    def available(self) -> bool:
        return self._client is not None

    def generate(self, prompt: str) -> str | None:
        if not self._client:
            return None
        try:
            response = self._client.text_generation(
                prompt,
                max_new_tokens=self.max_new_tokens,
                temperature=self.temperature,
                top_p=0.9,
                repetition_penalty=1.05,
            )
        except Exception:  # pragma: no cover - runtime safeguard
            return None
        return response.strip()

    def critique(self, headline: str, bullet_points: Sequence[str]) -> list[str]:
        if not bullet_points:
            return []
        prompt_lines = [self.system_prompt, "\nDecision Summary:", headline, "\nKey Signals:"]
        prompt_lines.extend(f"- {point}" for point in bullet_points)
        prompt_lines.append("\nRespond with numbered critiques highlighting actionable mitigations.")
        prompt = "\n".join(prompt_lines)
        output = self.generate(prompt)
        if not output:
            return []
        critiques: list[str] = []
        for line in output.splitlines():
            stripped = line.strip(" -")
            if not stripped:
                continue
            if stripped[0].isdigit() and "." in stripped:
                stripped = stripped.split(".", 1)[1].strip()
            critiques.append(stripped)
        return critiques


def merge_critiques(*critique_sets: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    merged: list[str] = []
    for critiques in critique_sets:
        for critique in critiques:
            normalised = critique.strip()
            if not normalised or normalised in seen:
                continue
            seen.add(normalised)
            merged.append(normalised)
    return merged


__all__ = ["DEFAULT_MODEL", "HuggingFaceCritiqueEngine", "merge_critiques"]
