from stratmaster_api.models import (
    Claim,
    EvidenceGrade,
    RetrievalRecord,
    RetrievalScore,
)

from stratmaster_cove import CoVeVerifier, VerificationStatus, run_cove


def _claim(claim_id: str, grade: EvidenceGrade, provenance: str) -> Claim:
    return Claim(
        id=claim_id,
        statement=f"Claim {claim_id}",
        evidence_grade=grade,
        provenance_ids=[provenance],
    )


def _retrieval(provenance: str) -> RetrievalRecord:
    return RetrievalRecord(
        document_id="doc-1",
        scores=RetrievalScore(hybrid_score=0.9),
        grounding_spans=[],
        chunk_hash="hash",
        provenance_id=provenance,
    )


def test_run_cove_marks_missing_provenance_as_failed():
    claims = [_claim("c1", EvidenceGrade.HIGH, "prov-1"), _claim("c2", EvidenceGrade.LOW, "prov-2")]
    result = run_cove(claims, retrieval=[_retrieval("prov-1")], minimum_pass_ratio=0.75)
    assert result.status == "needs_review"
    assert result.failed_questions == ["verify-002"]


def test_verifier_honours_minimum_pass_ratio():
    verifier = CoVeVerifier(minimum_pass_ratio=0.6)
    claims = [_claim("c1", EvidenceGrade.MODERATE, "prov-1"), _claim("c2", EvidenceGrade.MODERATE, "prov-2")]
    questions = verifier.plan(claims)
    answers = verifier.answer(questions, claims, [_retrieval("prov-1")])
    assert answers[0].status is VerificationStatus.PASSED
    assert answers[1].status is VerificationStatus.FAILED
    result = verifier.verify(claims, [_retrieval("prov-1")])
    assert result.status == "needs_review"
    assert result.verified_fraction == 0.5
