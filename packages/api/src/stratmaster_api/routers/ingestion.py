from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

try:
    from stratmaster_ingestion import DocumentPayload
    from stratmaster_ingestion.service import decode_base64
    INGESTION_AVAILABLE = True
except ImportError:
    # Graceful fallback when ingestion package is not available
    INGESTION_AVAILABLE = False
    DocumentPayload = None
    
    def decode_base64(data: str) -> bytes:
        import base64
        try:
            return base64.b64decode(data, validate=True)
        except Exception as exc:
            raise ValueError("Invalid base64 payload") from exc

from ..dependencies import require_idempotency_key
from ..models.ingestion import (
    ClarificationPromptResponse,
    ClarificationRequest,
    ClarificationResponse,
    IngestionChunkResponse,
    IngestionDocumentRequest,
    IngestionResponse,
)
from ..services import orchestrator_stub

router = APIRouter(prefix="/ingestion", tags=["ingestion"])


def _decode_payload(request: IngestionDocumentRequest) -> dict:
    try:
        content = decode_base64(request.content_base64)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    
    if not INGESTION_AVAILABLE:
        return {
            "filename": request.filename,
            "content": content,
            "tenant_id": request.tenant_id,
            "mimetype": request.mimetype,
        }
    
    return DocumentPayload(
        filename=request.filename,
        content=content,
        tenant_id=request.tenant_id,
        mimetype=request.mimetype,
    )


@router.post("/ingest", response_model=IngestionResponse)
async def ingest_document(
    payload: IngestionDocumentRequest,
    _: str = Depends(require_idempotency_key),
) -> IngestionResponse:
    if not INGESTION_AVAILABLE:
        raise HTTPException(
            status_code=503, 
            detail="Ingestion service unavailable - ingestion package not installed"
        )
    
    result = orchestrator_stub.ingest_document(_decode_payload(payload))
    return IngestionResponse(
        document_id=result.provenance.document_id,
        tenant_id=result.provenance.tenant_id,
        filename=result.provenance.filename,
        mimetype=result.provenance.mimetype,
        sha256=result.provenance.sha256,
        size_bytes=result.provenance.size_bytes,
        parser=result.provenance.parser,
        ingested_at=result.provenance.ingested_at,
        metrics=result.metrics.model_dump(),
        chunks=[
            IngestionChunkResponse(
                id=chunk.id,
                text=chunk.text,
                confidence=chunk.confidence,
                parser=chunk.metadata.parser,
                kind=chunk.metadata.kind.value,
                statistics=chunk.statistics.model_dump(),
            )
            for chunk in result.chunks
        ],
        needs_clarification=result.needs_clarification,
    )


@router.post("/clarify", response_model=ClarificationResponse)
async def clarify_document(
    payload: ClarificationRequest,
    _: str = Depends(require_idempotency_key),
) -> ClarificationResponse:
    if not INGESTION_AVAILABLE:
        raise HTTPException(
            status_code=503, 
            detail="Clarification service unavailable - ingestion package not installed"
        )
        
    prompts = orchestrator_stub.generate_clarifications(
        document_id=payload.document_id,
        chunks=[
            {
                "id": chunk.id,
                "confidence": chunk.confidence,
                "text": chunk.text,
                "kind": chunk.kind,
            }
            for chunk in payload.chunks
        ],
        threshold=payload.threshold,
    )
    return ClarificationResponse(
        document_id=payload.document_id,
        prompts=[ClarificationPromptResponse(**prompt) for prompt in prompts],
    )