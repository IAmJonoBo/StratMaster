from __future__ import annotations

import json
from pathlib import Path

import pytest


def _require_bge_cli_or_skip():
    try:  # lazy import to keep module importable
        from bge_reranker.cli import app as cli_app  # type: ignore
        from bge_reranker.models import RerankDocument, RerankRequest  # type: ignore
        from bge_reranker.scorer import BGEReranker  # type: ignore
        from typer.testing import CliRunner  # type: ignore
    except Exception:  # pragma: no cover - environment-dependent
        pytest.skip(
            "BGE reranker CLI dependencies not installed; skipping",
            allow_module_level=False,
        )
    return CliRunner, cli_app, RerankDocument, RerankRequest, BGEReranker


def test_reranker_orders_documents_by_similarity() -> None:
    _, _, rerank_document, rerank_request, bge_reranker = _require_bge_cli_or_skip()
    reranker = bge_reranker()
    request = rerank_request(
        query="premium strategy",
        documents=[
            rerank_document(id="a", text="Premium positioning and loyalty"),
            rerank_document(id="b", text="Operational cost reduction"),
        ],
        top_k=2,
    )
    results = reranker.rerank(request)
    assert results[0].id == "a"
    assert results[0].score > results[1].score


def test_cli_outputs_json(tmp_path: Path) -> None:
    cli_runner, cli_app, _, _, _ = _require_bge_cli_or_skip()
    docs = [
        {"id": "a", "text": "Premium positioning"},
        {"id": "b", "text": "Diagnostics"},
    ]
    docs_path = tmp_path / "docs.json"
    docs_path.write_text(json.dumps(docs), encoding="utf-8")

    runner = cli_runner()
    result = runner.invoke(
        cli_app,
        [
            "run",
            "--query",
            "premium",
            "--documents-path",
            str(docs_path),
            "--top-k",
            "1",
        ],
    )
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload[0]["id"] == "a"
