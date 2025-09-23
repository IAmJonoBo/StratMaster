"""Chain-of-Verification (CoVe) implementation for StratMaster."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from stratmaster_api.models import Claim, DebateTrace, DebateTurn, RetrievalRecord

from .state import StrategyState, ToolInvocation, ensure_agent_scratchpad
from .tools import ToolRegistry


@dataclass
class VerificationQuestion:
    """A question generated for verification of a claim."""
    id: str
    question: str
    claim_id: str
    verification_type: str  # "factual", "logical", "source"


@dataclass
class VerificationAnswer:
    """An answer to a verification question."""
    question_id: str
    answer: str
    confidence: float
    supporting_evidence: list[str]
    conflicts_detected: bool


@dataclass
class VerificationResult:
    """Result of Chain-of-Verification process."""
    questions: list[VerificationQuestion]
    answers: list[VerificationAnswer]
    verified_claims: list[str]  # IDs of claims that passed verification
    flagged_claims: list[str]   # IDs of claims that failed verification
    amendments: list[str]       # Suggested amendments to the draft
    overall_confidence: float


@dataclass
class ChainOfVerificationNode:
    """Chain-of-Verification node that validates claims before debate."""
    
    tools: ToolRegistry
    checkpoints: Any  # InMemoryCheckpointStore
    
    def __call__(self, state: StrategyState) -> StrategyState:
        """Run Chain-of-Verification process."""
        working = state.copy()
        pad = ensure_agent_scratchpad(working, "verification")
        
        # Generate verification questions
        verification_questions = self._generate_verification_questions(working.claims)
        
        # Answer verification questions independently
        verification_answers = self._answer_verification_questions(
            verification_questions, working.retrieval
        )
        
        # Analyze verification results
        verification_result = self._analyze_verification_results(
            verification_questions, verification_answers, working.claims
        )
        
        # Update state based on verification
        working = self._apply_verification_amendments(working, verification_result)
        
        # Record verification in debate trace
        if working.debate is None:
            working.debate = DebateTrace(turns=[])
        
        verification_content = self._format_verification_report(verification_result)
        working.debate.turns.append(
            DebateTurn(
                agent="verification",
                role="Synthesiser",  # CoVe runs between Synthesiser and Strategist
                content=verification_content,
                grounding=[],
            )
        )
        
        # Record telemetry
        pad.tool_calls.append(
            ToolInvocation(
                name="verification.cove",
                arguments={
                    "claim_count": len(working.claims),
                    "question_count": len(verification_questions),
                },
                response={
                    "verified_claims": len(verification_result.verified_claims),
                    "flagged_claims": len(verification_result.flagged_claims),
                    "amendments": len(verification_result.amendments),
                    "overall_confidence": verification_result.overall_confidence,
                },
            )
        )
        
        # Update metrics
        working.record_metric("verification_confidence", verification_result.overall_confidence)
        working.record_metric("claims_verified_ratio", 
                            len(verification_result.verified_claims) / max(len(working.claims), 1))
        
        pad.notes.append("Applied Chain-of-Verification with independent validation")
        self.checkpoints.save("verification", working)
        
        return working
    
    def _generate_verification_questions(self, claims: list[Claim]) -> list[VerificationQuestion]:
        """Generate verification questions for each claim."""
        questions = []
        
        for claim in claims:
            # Factual verification question
            questions.append(VerificationQuestion(
                id=f"factual-{claim.id}",
                question=f"Can this claim be factually verified: '{claim.statement}'?",
                claim_id=claim.id,
                verification_type="factual"
            ))
            
            # Source verification question  
            if claim.provenance_ids:
                questions.append(VerificationQuestion(
                    id=f"source-{claim.id}",
                    question=f"Do the cited sources actually support this claim: '{claim.statement}'?",
                    claim_id=claim.id,
                    verification_type="source"
                ))
            
            # Logical consistency question
            questions.append(VerificationQuestion(
                id=f"logical-{claim.id}",
                question=f"Is this claim logically consistent with other findings: '{claim.statement}'?",
                claim_id=claim.id,
                verification_type="logical"
            ))
        
        return questions
    
    def _answer_verification_questions(
        self, 
        questions: list[VerificationQuestion], 
        retrieval: list[RetrievalRecord]
    ) -> list[VerificationAnswer]:
        """Answer verification questions independently using retrieval context."""
        answers = []
        
        for question in questions:
            # Find relevant retrieval records
            relevant_records = [
                record for record in retrieval 
                if any(span.source_id in question.question for span in record.grounding_spans)
            ]
            
            # Generate answer based on question type
            answer = self._generate_verification_answer(question, relevant_records)
            answers.append(answer)
        
        return answers
    
    def _generate_verification_answer(
        self, 
        question: VerificationQuestion, 
        records: list[RetrievalRecord]
    ) -> VerificationAnswer:
        """Generate an answer for a verification question."""
        
        # Simulate verification logic (in real implementation, this would use LLM)
        base_confidence = 0.7
        supporting_evidence = [record.document_id for record in records[:2]]
        
        # Adjust confidence based on verification type and available evidence
        if question.verification_type == "factual":
            confidence = base_confidence + (0.1 if records else -0.2)
            answer = "Claim appears factually accurate based on available evidence" if records else "Insufficient evidence to verify claim"
        elif question.verification_type == "source":
            confidence = base_confidence + (0.15 if len(records) >= 2 else -0.3)
            answer = "Sources adequately support the claim" if len(records) >= 2 else "Sources provide insufficient support"
        else:  # logical
            confidence = base_confidence
            answer = "Claim is logically consistent with other findings"
        
        conflicts_detected = confidence < 0.5
        
        return VerificationAnswer(
            question_id=question.id,
            answer=answer,
            confidence=max(0.1, min(0.9, confidence)),
            supporting_evidence=supporting_evidence,
            conflicts_detected=conflicts_detected
        )
    
    def _analyze_verification_results(
        self, 
        questions: list[VerificationQuestion], 
        answers: list[VerificationAnswer],
        claims: list[Claim]
    ) -> VerificationResult:
        """Analyze verification results and determine amendments needed."""
        
        verified_claims = []
        flagged_claims = []
        amendments = []
        
        # Group answers by claim
        claim_answers = {}
        for answer in answers:
            question = next(q for q in questions if q.id == answer.question_id)
            claim_id = question.claim_id
            if claim_id not in claim_answers:
                claim_answers[claim_id] = []
            claim_answers[claim_id].append(answer)
        
        # Analyze each claim
        for claim in claims:
            claim_answers_list = claim_answers.get(claim.id, [])
            
            # Calculate claim verification confidence
            if claim_answers_list:
                avg_confidence = sum(a.confidence for a in claim_answers_list) / len(claim_answers_list)
                has_conflicts = any(a.conflicts_detected for a in claim_answers_list)
                
                if avg_confidence >= 0.7 and not has_conflicts:
                    verified_claims.append(claim.id)
                else:
                    flagged_claims.append(claim.id)
                    
                    # Generate amendments for flagged claims
                    if has_conflicts:
                        amendments.append(f"Resolve conflicting evidence for claim: {claim.statement[:50]}...")
                    if avg_confidence < 0.7:
                        amendments.append(f"Strengthen evidence for claim: {claim.statement[:50]}...")
        
        # Calculate overall confidence
        overall_confidence = len(verified_claims) / max(len(claims), 1)
        
        return VerificationResult(
            questions=questions,
            answers=answers,
            verified_claims=verified_claims,
            flagged_claims=flagged_claims,
            amendments=amendments,
            overall_confidence=overall_confidence
        )
    
    def _apply_verification_amendments(
        self, state: StrategyState, result: VerificationResult
    ) -> StrategyState:
        """Apply verification amendments to the state."""
        
        # Remove or mark flagged claims
        if result.flagged_claims:
            # In a real implementation, we might modify or remove flagged claims
            # For now, we record them as needing review
            for flagged_id in result.flagged_claims:
                state.mark_failed(f"Claim verification failed: {flagged_id}")
        
        # Record amendments as notes for future processing
        if result.amendments:
            pad = ensure_agent_scratchpad(state, "verification")
            pad.notes.extend(result.amendments)
        
        return state
    
    def _format_verification_report(self, result: VerificationResult) -> str:
        """Format verification results as a readable report."""
        report_parts = [
            "CHAIN-OF-VERIFICATION REPORT",
            f"Claims analyzed: {len(result.questions) // 3}",  # 3 questions per claim
            f"Claims verified: {len(result.verified_claims)}",
            f"Claims flagged: {len(result.flagged_claims)}",
            f"Overall confidence: {result.overall_confidence:.2f}",
        ]
        
        if result.amendments:
            report_parts.append("\nRECOMMENDED AMENDMENTS:")
            for amendment in result.amendments:
                report_parts.append(f"- {amendment}")
        
        if result.verified_claims:
            report_parts.append(f"\n✓ Verified claims: {', '.join(result.verified_claims)}")
        
        if result.flagged_claims:
            report_parts.append(f"\n⚠ Flagged claims: {', '.join(result.flagged_claims)}")
        
        return "\n".join(report_parts)