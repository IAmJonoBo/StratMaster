from __future__ import annotations

import base64

import pytest

from stratmaster_ingestion import (
    ClarificationService,
    DocumentPayload,
    IngestionCoordinator,
)


@pytest.fixture()
def coordinator() -> IngestionCoordinator:
    return IngestionCoordinator()


def test_ingest_plain_text_document(coordinator: IngestionCoordinator) -> None:
    payload = DocumentPayload(
        filename="memo.txt",
        content=b"StratMaster delivers grounded strategic recommendations backed by evidence.",
        tenant_id="tenant-a",
        mimetype="text/plain",
    )
    result = coordinator.ingest(payload)
    assert result.provenance.filename == "memo.txt"
    assert result.metrics.overall_confidence > 0.6
    assert len(result.chunks) == 1
    chunk = result.chunks[0]
    assert chunk.metadata.parser == "plain-text"
    assert chunk.statistics.word_count >= 8


def test_ingest_csv_generates_table_chunks(coordinator: IngestionCoordinator) -> None:
    payload = DocumentPayload(
        filename="table.csv",
        content=b"column_a,column_b\nvalue1,value2",
        tenant_id="tenant-a",
        mimetype="text/csv",
    )
    result = coordinator.ingest(payload)
    assert len(result.chunks) == 2
    kinds = {chunk.metadata.kind.value for chunk in result.chunks}
    assert kinds == {"table"}


def test_low_confidence_triggers_clarification() -> None:
    payload = DocumentPayload(
        filename="scan.txt",
        content="""XXXX 000 ???
@@@
""".encode("utf-8"),
        tenant_id="tenant-a",
        mimetype="text/plain",
    )
    coordinator = IngestionCoordinator()
    result = coordinator.ingest(payload)
    assert result.metrics.low_confidence_chunks >= 1
    clarifier = ClarificationService()
    plan = clarifier.for_result(result)
    assert plan.requires_follow_up is True
    prompt = plan.prompts[0]
    assert "noisy" in prompt.question.lower()


def test_decode_base64_helper_handles_invalid_payload() -> None:
    from stratmaster_ingestion.service import decode_base64

    with pytest.raises(ValueError):
        decode_base64("not-base64")

    data = base64.b64encode(b"hello").decode()
    assert decode_base64(data) == b"hello"