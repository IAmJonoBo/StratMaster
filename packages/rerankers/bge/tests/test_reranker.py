from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from bge_reranker.cli import app as cli_app
from bge_reranker.models import RerankDocument, RerankRequest
from bge_reranker.scorer import BGEReranker


def test_reranker_orders_documents_by_similarity() -> None:
    reranker = BGEReranker()
    request = RerankRequest(
        query="premium strategy",
        documents=[
            RerankDocument(id="a", text="Premium positioning and loyalty"),
            RerankDocument(id="b", text="Operational cost reduction"),
        ],
        top_k=2,
    )
    results = reranker.rerank(request)
    assert results[0].id == "a"
    assert results[0].score > results[1].score


def test_cli_outputs_json(tmp_path: Path) -> None:
    docs = [
        {"id": "a", "text": "Premium positioning"},
        {"id": "b", "text": "Diagnostics"},
    ]
    docs_path = tmp_path / "docs.json"
    docs_path.write_text(json.dumps(docs), encoding="utf-8")

    runner = CliRunner()
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
