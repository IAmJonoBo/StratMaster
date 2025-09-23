"""Clarification workflow for low-confidence chunks."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from pydantic import BaseModel, ConfigDict, Field

from .models import DocumentChunk, ParseResult


class ClarificationPrompt(BaseModel):
    """Single clarifying question for a low-confidence chunk."""

    model_config = ConfigDict(extra="forbid")

    chunk_id: str
    question: str
    rationale: str
    suggested_action: str
    confidence: float = Field(ge=0.0, le=1.0)
    threshold: float = Field(ge=0.0, le=1.0)


class ClarificationPlan(BaseModel):
    """Aggregate plan covering all clarification prompts."""

    model_config = ConfigDict(extra="forbid")

    document_id: str
    prompts: list[ClarificationPrompt]

    @property
    def requires_follow_up(self) -> bool:
        return bool(self.prompts)


@dataclass(slots=True)
class ClarificationInput:
    chunk_id: str
    confidence: float
    text: str
    kind: str


class ClarificationService:
    """Generate clarifying prompts when confidence thresholds are breached."""

    def __init__(self, threshold: float = 0.7) -> None:
        self.threshold = threshold

    def build_plan(
        self,
        *,
        document_id: str,
        chunks: Iterable[DocumentChunk],
        threshold: float | None = None,
    ) -> ClarificationPlan:
        prompts = [
            self._prompt_from_chunk(chunk, threshold or self.threshold)
            for chunk in chunks
            if chunk.confidence < (threshold or self.threshold)
        ]
        return ClarificationPlan(document_id=document_id, prompts=prompts)

    def from_inputs(
        self,
        *,
        document_id: str,
        inputs: Iterable[ClarificationInput],
        threshold: float | None = None,
    ) -> ClarificationPlan:
        prompts: list[ClarificationPrompt] = []
        active_threshold = threshold or self.threshold
        for item in inputs:
            if item.confidence >= active_threshold:
                continue
            prompts.append(
                ClarificationPrompt(
                    chunk_id=item.chunk_id,
                    confidence=round(item.confidence, 4),
                    threshold=round(active_threshold, 4),
                    question=self._build_question(item),
                    rationale=self._build_rationale(item),
                    suggested_action=self._suggest_action(item),
                )
            )
        return ClarificationPlan(document_id=document_id, prompts=prompts)

    def for_result(self, result: ParseResult, threshold: float | None = None) -> ClarificationPlan:
        return self.build_plan(
            document_id=result.provenance.document_id,
            chunks=result.low_confidence(),
            threshold=threshold,
        )

    @staticmethod
    def _prompt_from_chunk(chunk: DocumentChunk, threshold: float) -> ClarificationPrompt:
        return ClarificationPrompt(
            chunk_id=chunk.id,
            confidence=round(chunk.confidence, 4),
            threshold=round(threshold, 4),
            question=ClarificationService._build_question(
                ClarificationInput(
                    chunk_id=chunk.id,
                    confidence=chunk.confidence,
                    text=chunk.text,
                    kind=chunk.metadata.kind.value,
                )
            ),
            rationale=ClarificationService._build_rationale(
                ClarificationInput(
                    chunk_id=chunk.id,
                    confidence=chunk.confidence,
                    text=chunk.text,
                    kind=chunk.metadata.kind.value,
                )
            ),
            suggested_action=ClarificationService._suggest_action(
                ClarificationInput(
                    chunk_id=chunk.id,
                    confidence=chunk.confidence,
                    text=chunk.text,
                    kind=chunk.metadata.kind.value,
                )
            ),
        )

    @staticmethod
    def _build_question(item: ClarificationInput) -> str:
        kind = "table" if item.kind == "table" else "content"
        return (
            f"Chunk {item.chunk_id} {kind} looks noisy. Could you share a clearer source, "
            "additional context, or confirm the key facts?"
        )

    @staticmethod
    def _build_rationale(item: ClarificationInput) -> str:
        if not item.text.strip():
            return "No readable text detected in the chunk."
        snippet = item.text.strip().splitlines()[0][:160]
        return (
            "Heuristic scoring flagged the chunk as low confidence based on limited tokens "
            f"and noisy characters (sample: '{snippet}')."
        )

    @staticmethod
    def _suggest_action(item: ClarificationInput) -> str:
        if item.kind == "table":
            return "Upload the original spreadsheet or provide the table values in plain text."
        if not item.text.strip():
            return "Provide a higher-resolution scan or re-upload a text-based version."
        return "Confirm the transcription or supply supporting context for verification."

