"""Query a ColBERT index."""

from __future__ import annotations

from pathlib import Path

import typer

from .config import load_config
from .indexer import ColbertIndex, embed_query, score

app = typer.Typer(help="Query a previously materialised ColBERT index")


def search_index(index: ColbertIndex, query: str, k: int) -> list[tuple[str, float]]:
    query_vector = embed_query(query, index.dim)
    ranked = [(doc.doc_id, score(query_vector, doc.vector)) for doc in index.documents]
    ranked.sort(key=lambda item: item[1], reverse=True)
    return ranked[:k]


def _run_query(config: Path, index_path: Path, query: str, top_k: int | None) -> None:
    cfg = load_config(config)
    index = ColbertIndex.load(index_path)
    limit = top_k or cfg.search.k
    results = search_index(index, query=query, k=limit)
    for doc_id, score_value in results:
        typer.echo(f"{doc_id}\t{score_value:.4f}")


@app.callback()
def main(
    ctx: typer.Context,
    config: Path = typer.Option(None, exists=True, readable=True),
    index_path: Path = typer.Option(None, exists=True, dir_okay=False, file_okay=True),
    query: str = typer.Option(None),
    top_k: int | None = typer.Option(None, min=1, max=100),
) -> None:
    if ctx.invoked_subcommand is not None:
        return
    if None in (config, index_path, query):
        raise typer.BadParameter("--config, --index-path, and --query are required")
    _run_query(config, index_path, query, top_k)


@app.command()
def query(
    config: Path = typer.Option(..., exists=True, readable=True),
    index_path: Path = typer.Option(..., exists=True, dir_okay=False, file_okay=True),
    query: str = typer.Option(...),
    top_k: int | None = typer.Option(None, min=1, max=100),
) -> None:
    _run_query(config, index_path, query, top_k)


if __name__ == "__main__":  # pragma: no cover
    app()
