"""Typed structures for the Chain-of-Verification flow."""

from __future__ import annotations

from enum import Enum
from typing import Iterable, Literal, Sequence

from pydantic import BaseModel, ConfigDict, Field


class VerificationStatus(str, Enum):
    """Outcome of a verification question."""

    PASSED = "passed"
    FAILED = "failed"


class VerificationQuestion(BaseModel):
    """Structured verification prompt planned for a claim or step."""

    model_config = ConfigDict(extra="forbid")

    id: str
    claim_id: str
    question: str
    expected_answer: Literal["boolean", "text"] = "boolean"
    guidance: str | None = None


class VerificationAnswer(BaseModel):
    """Result emitted by the verifier for a single question."""

    model_config = ConfigDict(extra="forbid")

    question_id: str
    status: VerificationStatus
    answer: str
    citations: list[str] = Field(default_factory=list)
    rationale: str | None = None


class VerificationResult(BaseModel):
    """Aggregated verification outcome."""

    model_config = ConfigDict(extra="forbid")

    questions: list[VerificationQuestion]
    answers: list[VerificationAnswer]
    verified_fraction: float = Field(..., ge=0.0, le=1.0)
    failed_questions: list[str] = Field(default_factory=list)
    status: Literal["verified", "needs_review"]

    @classmethod
    def from_answers(
        cls,
        questions: Sequence[VerificationQuestion],
        answers: Sequence[VerificationAnswer],
        minimum_pass_ratio: float,
    ) -> "VerificationResult":
        """Build a result from questions and their answers."""

        question_index = {q.id: q for q in questions}
        failed: list[str] = []
        passed = 0
        normalised_answers: list[VerificationAnswer] = []
        for answer in answers:
            if answer.question_id not in question_index:
                # Ignore stray answers; they should not affect pass ratio
                continue
            normalised_answers.append(answer)
            if answer.status is VerificationStatus.PASSED:
                passed += 1
            else:
                failed.append(answer.question_id)
        total = len(questions)
        ratio = (passed / total) if total else 1.0
        status: Literal["verified", "needs_review"]
        status = "verified" if ratio >= minimum_pass_ratio else "needs_review"
        return cls(
            questions=list(questions),
            answers=normalised_answers,
            verified_fraction=ratio,
            failed_questions=failed,
            status=status,
        )


def default_verification_guidance(claim_statement: str) -> str:
    """Derive short guidance for a claim."""

    return (
        "Confirm the claim using independent evidence and highlight discrepancies "
        f"if the available sources contradict: {claim_statement}"
    )


def build_questions_for_claims(
    claim_ids: Iterable[str],
    claim_statements: Iterable[str],
    prefix: str = "verify",
) -> list[VerificationQuestion]:
    """Generate deterministic verification questions for claims."""

    questions: list[VerificationQuestion] = []

    for idx, (claim_id, statement) in enumerate(zip(claim_ids, claim_statements, strict=False), start=1):

        questions.append(
            VerificationQuestion(
                id=f"{prefix}-{idx:03d}",
                claim_id=claim_id,
                question=f"Does the evidence support the claim '{statement}'?",
                expected_answer="boolean",
                guidance=default_verification_guidance(statement),
            )
        )
    return questions
