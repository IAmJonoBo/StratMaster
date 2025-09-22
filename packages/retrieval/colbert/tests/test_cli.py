from __future__ import annotations

import json
from pathlib import Path

import pytest


def _require_colbert_cli_or_skip():
    try:  # lazy import to keep module importable
        from colbert.config import ColbertConfig  # type: ignore
        from colbert.eval import app as eval_app  # type: ignore
        from colbert.index import app as index_app  # type: ignore
        from colbert.indexer import ColbertIndex, ColbertIndexer  # type: ignore
        from colbert.search import app as search_app  # type: ignore
        from typer.testing import CliRunner  # type: ignore
    except Exception:  # pragma: no cover - environment-dependent
        pytest.skip(
            "ColBERT CLI dependencies not installed; skipping",
            allow_module_level=False,
        )
    return (
        CliRunner,
        ColbertConfig,
        eval_app,
        index_app,
        ColbertIndex,
        ColbertIndexer,
        search_app,
    )


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
    (
        cli_runner,
        colbert_config,
        _eval_app,
        index_app,
        colbert_index,
        colbert_indexer,
        _search_app,
    ) = _require_colbert_cli_or_skip()
    runner = cli_runner()
    corpus_path = _write_corpus(tmp_path)
    config_path = _write_config(tmp_path, corpus_path)

    result = runner.invoke(index_app, ["build", "--config", str(config_path)])
    assert result.exit_code == 0
    output_dir = tmp_path / "artifacts" / "demo-index"
    index_file = output_dir / "index.json"
    assert index_file.exists()

    index = colbert_index.load(index_file)
    assert len(index.documents) == 2


def test_search_cli_returns_ranked_docs(tmp_path: Path) -> None:
    corpus_path = _write_corpus(tmp_path)
    config_path = _write_config(tmp_path, corpus_path)
    (
        cli_runner,
        colbert_config,
        _eval_app,
        _index_app,
        colbert_index,
        colbert_indexer,
        search_app,
    ) = _require_colbert_cli_or_skip()
    indexer = colbert_indexer(colbert_config(**json.loads(config_path.read_text())))
    index_path = indexer.materialise(tmp_path / "artifacts" / "demo-index")

    runner = cli_runner()
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
    (
        cli_runner,
        colbert_config,
        eval_app,
        _index_app,
        _colbert_index,
        colbert_indexer,
        _search_app,
    ) = _require_colbert_cli_or_skip()
    indexer = colbert_indexer(colbert_config(**json.loads(config_path.read_text())))
    index_path = indexer.materialise(tmp_path / "artifacts" / "demo-index")

    queries = [{"query": "premium", "relevant": ["doc-1"]}]
    queries_path = tmp_path / "queries.json"
    queries_path.write_text(json.dumps(queries), encoding="utf-8")

    runner = cli_runner()
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
