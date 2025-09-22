from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from splade.config import SpladeConfig
from splade.expand import app as expand_app
from splade.index import app as index_app
from splade.verify import app as verify_app
from splade.indexer import SpladeIndex, SpladeIndexer


def _write_config(tmp_path: Path, corpus_path: Path) -> Path:
    config = {
        "corpus": {"path": str(corpus_path), "text_fields": ["summary", "title"]},
        "index": {"name": "splade-index"},
        "model": {"name": "splade", "max_document_length": 256},
        "search": {"k": 10, "pruning_threshold": 0.001},
        "storage": {"output_dir": str(tmp_path / "artifacts")},
    }
    config_path = tmp_path / "splade.yaml"
    config_path.write_text(json.dumps(config), encoding="utf-8")
    return config_path


def _write_corpus(tmp_path: Path) -> Path:
    corpus = {
        "documents": [
            {
                "id": "doc-1",
                "title": "Premium loyalty",
                "summary": "Concierge onboarding for premium cohorts",
            },
            {
                "id": "doc-2",
                "title": "Diagnostics",
                "summary": "Journey diagnostics improve retention",
            },
        ]
    }
    corpus_path = tmp_path / "corpus.json"
    corpus_path.write_text(json.dumps(corpus), encoding="utf-8")
    return corpus_path


def test_expand_cli_writes_jsonl(tmp_path: Path) -> None:
    runner = CliRunner()
    corpus_path = _write_corpus(tmp_path)
    config_path = _write_config(tmp_path, corpus_path)
    output_path = tmp_path / "expansions.jsonl"

    result = runner.invoke(
        expand_app,
        ["run", "--config", str(config_path), "--output", str(output_path), "--max-features", "50"],
    )
    assert result.exit_code == 0
    assert output_path.exists()
    lines = output_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2


def test_index_cli_materialises_index(tmp_path: Path) -> None:
    corpus_path = _write_corpus(tmp_path)
    config_path = _write_config(tmp_path, corpus_path)
    indexer = SpladeIndexer(SpladeConfig(**json.loads(config_path.read_text())))
    index_path = indexer.materialise(tmp_path / "artifacts" / "splade-index")

    runner = CliRunner()
    result = runner.invoke(
        index_app,
        ["build", "--config", str(config_path), "--output", str(tmp_path / "artifacts" / "splade-index")],
    )
    assert result.exit_code == 0
    persisted = SpladeIndex.load(index_path)
    assert len(persisted.documents) == 2


def test_verify_cli_confirms_alignment(tmp_path: Path) -> None:
    corpus_path = _write_corpus(tmp_path)
    config_path = _write_config(tmp_path, corpus_path)
    expander_runner = CliRunner()
    expansions_path = tmp_path / "expansions.jsonl"
    expander_runner.invoke(
        expand_app,
        ["run", "--config", str(config_path), "--output", str(expansions_path)],
    )
    indexer = SpladeIndexer(SpladeConfig(**json.loads(config_path.read_text())))
    index_path = indexer.materialise(tmp_path / "artifacts" / "splade-index")

    runner = CliRunner()
    result = runner.invoke(
        verify_app,
        [
            "run",
            "--config",
            str(config_path),
            "--index-path",
            str(index_path),
            "--expansions-path",
            str(expansions_path),
        ],
    )
    assert result.exit_code == 0
    assert "All expansions" in result.stdout
