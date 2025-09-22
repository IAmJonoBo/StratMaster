from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from colbert.config import ColbertConfig
from colbert.index import app as index_app
from colbert.search import app as search_app
from colbert.eval import app as eval_app
from colbert.indexer import ColbertIndex, ColbertIndexer


def _write_config(tmp_path: Path, corpus_path: Path) -> Path:
    config = {
        "corpus": {"path": str(corpus_path), "text_fields": ["summary", "title"]},
        "index": {"name": "demo-index", "shards": 1},
        "embedding": {"model": "demo", "dim": 64},
        "search": {"k": 5, "alpha_dense_sparse_mix": 0.7},
        "storage": {"output_dir": str(tmp_path / "artifacts")},
    }
    config_path = tmp_path / "colbert.yaml"
    config_path.write_text(json.dumps(config), encoding="utf-8")
    return config_path


def _write_corpus(tmp_path: Path) -> Path:
    corpus = {
        "documents": [
            {
                "id": "doc-1",
                "title": "Premium strategy",
                "summary": "Premium positioning playbook",
            },
            {
                "id": "doc-2",
                "title": "Retention strategy",
                "summary": "Improve retention through diagnostics",
            },
        ]
    }
    corpus_path = tmp_path / "corpus.json"
    corpus_path.write_text(json.dumps(corpus), encoding="utf-8")
    return corpus_path


def test_build_cli_materialises_index(tmp_path: Path) -> None:
    runner = CliRunner()
    corpus_path = _write_corpus(tmp_path)
    config_path = _write_config(tmp_path, corpus_path)

    result = runner.invoke(index_app, ["build", "--config", str(config_path)])
    assert result.exit_code == 0
    output_dir = tmp_path / "artifacts" / "demo-index"
    index_file = output_dir / "index.json"
    assert index_file.exists()

    index = ColbertIndex.load(index_file)
    assert len(index.documents) == 2


def test_search_cli_returns_ranked_docs(tmp_path: Path) -> None:
    corpus_path = _write_corpus(tmp_path)
    config_path = _write_config(tmp_path, corpus_path)
    indexer = ColbertIndexer(ColbertConfig(**json.loads(config_path.read_text())))
    index_path = indexer.materialise(tmp_path / "artifacts" / "demo-index")

    runner = CliRunner()
    result = runner.invoke(
        search_app,
        [
            "query",
            "--config",
            str(config_path),
            "--index-path",
            str(index_path),
            "--query",
            "premium positioning",
            "--top-k",
            "1",
        ],
    )
    assert result.exit_code == 0
    assert "doc-1" in result.stdout


def test_eval_cli_reports_recall(tmp_path: Path) -> None:
    corpus_path = _write_corpus(tmp_path)
    config_path = _write_config(tmp_path, corpus_path)
    indexer = ColbertIndexer(ColbertConfig(**json.loads(config_path.read_text())))
    index_path = indexer.materialise(tmp_path / "artifacts" / "demo-index")

    queries = [{"query": "premium", "relevant": ["doc-1"]}]
    queries_path = tmp_path / "queries.json"
    queries_path.write_text(json.dumps(queries), encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(
        eval_app,
        [
            "run",
            "--config",
            str(config_path),
            "--index-path",
            str(index_path),
            "--queries-path",
            str(queries_path),
        ],
    )
    assert result.exit_code == 0
    assert "Mean Recall" in result.stdout
