"""Evaluation helpers for the ColBERT index."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import typer

from .config import load_config
from .indexer import ColbertIndex
from .search import search_index

app = typer.Typer(help="Evaluate retrieval quality for the ColBERT index")


@dataclass(slots=True)
class EvalResult:
    query: str
    relevant: set[str]
    retrieved: list[tuple[str, float]]

    def recall(self, k: int) -> float:
        top_docs = {doc_id for doc_id, _ in self.retrieved[:k]}
        if not self.relevant:
            return 1.0
        return len(self.relevant & top_docs) / len(self.relevant)


def _run_eval(
    config: Path, index_path: Path, queries_path: Path, top_k: int | None
) -> None:
    cfg = load_config(config)
    index = ColbertIndex.load(index_path)
    limit = top_k or cfg.search.k
    queries = json.loads(queries_path.read_text(encoding="utf-8"))
    if not isinstance(queries, list):
        raise ValueError(
            "queries file must contain a list of {query, relevant} objects"
        )

    scores: list[EvalResult] = []
    for item in queries:
        query = item.get("query")
        relevant = set(map(str, item.get("relevant", [])))
        retrieved = search_index(index, query, k=limit)
        scores.append(EvalResult(query=query, relevant=relevant, retrieved=retrieved))

    recall_values = [result.recall(limit) for result in scores]
    mean_recall = sum(recall_values) / len(recall_values) if recall_values else 0.0
    typer.echo(f"Mean Recall@{limit}: {mean_recall:.3f}")


@app.callback()
def main(
    ctx: typer.Context,
    config: Path = typer.Option(None, exists=True, readable=True),
    index_path: Path = typer.Option(None, exists=True, dir_okay=False, file_okay=True),
    queries_path: Path = typer.Option(
        None, exists=True, dir_okay=False, file_okay=True
    ),
    top_k: int | None = typer.Option(None, min=1, max=100),
) -> None:
    if ctx.invoked_subcommand is not None:
        return
    if None in (config, index_path, queries_path):
        raise typer.BadParameter(
            "--config, --index-path, and --queries-path are required"
        )
    _run_eval(config, index_path, queries_path, top_k)


@app.command()
def run(
    config: Path = typer.Option(..., exists=True, readable=True),
    index_path: Path = typer.Option(..., exists=True, dir_okay=False, file_okay=True),
    queries_path: Path = typer.Option(..., exists=True, dir_okay=False, file_okay=True),
    top_k: int | None = typer.Option(None, min=1, max=100),
) -> None:
    _run_eval(config, index_path, queries_path, top_k)


if __name__ == "__main__":  # pragma: no cover
    app()
