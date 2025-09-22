"""Deterministic Chain-of-Verification (CoVe) planner and verifier."""

from __future__ import annotations

from collections.abc import Iterable, Sequence

from stratmaster_api.models import Claim, EvidenceGrade, RetrievalRecord

from .types import (
    VerificationAnswer,
    VerificationQuestion,
    VerificationResult,
    VerificationStatus,
    build_questions_for_claims,
)


class CoVeVerifier:
    """Plan verification questions and synthesise deterministic answers."""

    def __init__(self, minimum_pass_ratio: float = 0.8) -> None:
        if not 0 < minimum_pass_ratio <= 1:
            raise ValueError("minimum_pass_ratio must be within (0, 1]")
        self.minimum_pass_ratio = minimum_pass_ratio

    def plan(self, claims: Sequence[Claim]) -> list[VerificationQuestion]:
        claim_ids = [claim.id for claim in claims]
        statements = [claim.statement for claim in claims]
        return build_questions_for_claims(claim_ids, statements)

    def answer(
        self,
        questions: Sequence[VerificationQuestion],
        claims: Sequence[Claim],
        retrieval: Iterable[RetrievalRecord] | None = None,
    ) -> list[VerificationAnswer]:
        """Produce deterministic answers based on evidence grades and retrieval."""

        provenance_index: set[str] = set()
        if retrieval is not None:
            for record in retrieval:
                provenance_index.add(record.provenance_id)

        claim_lookup = {claim.id: claim for claim in claims}
        answers: list[VerificationAnswer] = []
        for question in questions:
            claim = claim_lookup.get(question.claim_id)
            if claim is None:
                continue
            has_provenance_overlap = any(
                prov in provenance_index for prov in claim.provenance_ids
            )
            status = self._status_from_claim(claim, has_provenance_overlap)
            rationale = (
                "Evidence aligns with recorded provenance"
                if status is VerificationStatus.PASSED
                else "Insufficient evidence strength"
            )
            answers.append(
                VerificationAnswer(
                    question_id=question.id,
                    status=status,
                    answer="yes" if status is VerificationStatus.PASSED else "no",
                    citations=list(claim.provenance_ids[:2]),
                    rationale=rationale,
                )
            )
        return answers

    def verify(
        self,
        claims: Sequence[Claim],
        retrieval: Iterable[RetrievalRecord] | None = None,
    ) -> VerificationResult:
        questions = self.plan(claims)
        answers = self.answer(questions, claims, retrieval)
        return VerificationResult.from_answers(
            questions, answers, minimum_pass_ratio=self.minimum_pass_ratio
        )

    @staticmethod
    def _status_from_claim(
        claim: Claim, has_provenance_overlap: bool
    ) -> VerificationStatus:
        if claim.evidence_grade is EvidenceGrade.HIGH and has_provenance_overlap:
            return VerificationStatus.PASSED
        if claim.evidence_grade is EvidenceGrade.MODERATE and has_provenance_overlap:
            return VerificationStatus.PASSED
        return VerificationStatus.FAILED


def run_cove(
    claims: Sequence[Claim],
    retrieval: Iterable[RetrievalRecord] | None = None,
    minimum_pass_ratio: float = 0.8,
) -> VerificationResult:
    """Convenience helper used by orchestrator nodes."""

    verifier = CoVeVerifier(minimum_pass_ratio=minimum_pass_ratio)
    return verifier.verify(claims=claims, retrieval=retrieval)
