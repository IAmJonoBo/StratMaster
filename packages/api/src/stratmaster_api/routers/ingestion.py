from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from stratmaster_ingestion import DocumentPayload
from stratmaster_ingestion.service import decode_base64

from ..dependencies import require_idempotency_key
from ..models.ingestion import (
    ClarificationRequest,
    ClarificationResponse,
    ClarificationPromptResponse,
    IngestionDocumentRequest,
    IngestionResponse,
    IngestionChunkResponse,
)
from ..services import orchestrator_stub

router = APIRouter(prefix="/ingestion", tags=["ingestion"])


def _decode_payload(request: IngestionDocumentRequest) -> DocumentPayload:
    try:
        content = decode_base64(request.content_base64)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
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

