from __future__ import annotations

import json
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from rerankers.bge import BGEReranker
from rerankers.bge.cli import main as cli_main
from rerankers.bge.service import create_app


@pytest.fixture(autouse=True)
def force_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RERANKERS_BGE_FORCE_FALLBACK", "1")


def test_reranker_orders_candidates() -> None:
    reranker = BGEReranker(force_fallback=True)
    query = "premium positioning strategy"
    candidates = [
        "Invest in premium positioning to lift revenue",
        "Commoditised offerings continue to grow",
        "Premium strategy delivers loyalty",
    ]
    scores = reranker.score(query, candidates)
    assert scores[0] > scores[1]
    ranked = reranker.rerank(query, candidates)
    assert ranked[0].text.startswith("Invest in premium")
    assert ranked[0].score >= ranked[1].score


def test_cli_outputs_ranked_json(tmp_path: Path) -> None:
    candidates_path = tmp_path / "candidates.json"
    candidates_path.write_text(
        json.dumps(["premium demand", "cost cutting", "premium loyalty"]),
        encoding="utf-8",
    )
    buffer = StringIO()
    with redirect_stdout(buffer):
        cli_main(
            [
                "--query",
                "premium strategy",
                "--candidates",
                str(candidates_path),
                "--force-fallback",
                "--top-k",
                "2",
            ]
        )
    output = json.loads(buffer.getvalue())
    assert len(output) == 2
    assert output[0]["score"] >= output[1]["score"]


def test_service_endpoint_returns_scores() -> None:
    app = create_app(BGEReranker(force_fallback=True))
    client = TestClient(app)
    response = client.post(
        "/rerank",
        json={
            "query": "premium positioning",
            "candidates": ["premium wins", "value focus"],
            "top_k": 1,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["results"][0]["text"] == "premium wins"
    assert payload["results"][0]["score"] > 0
