"""CLI wrapper around the deterministic BGE reranker."""

from __future__ import annotations

import json
from pathlib import Path

import typer

from .models import RerankDocument, RerankRequest
from .scorer import BGEReranker

app = typer.Typer(help="Run BGE reranking on a JSON payload")


def _run_cli(query: str, documents_path: Path, top_k: int) -> None:
    documents_raw = json.loads(documents_path.read_text(encoding="utf-8"))
    docs = [RerankDocument(**item) for item in documents_raw]
    request = RerankRequest(query=query, documents=docs, top_k=top_k)
    reranker = BGEReranker()
    results = reranker.rerank(request)
    typer.echo(json.dumps([result.model_dump() for result in results]))


@app.callback()
def main(
    ctx: typer.Context,
    query: str = typer.Option(None, help="Query to rerank against"),
    documents_path: Path = typer.Option(None, exists=True, dir_okay=False, file_okay=True),
    top_k: int = typer.Option(5, min=1, max=50),
) -> None:
    if ctx.invoked_subcommand is not None:
        return
    if query is None or documents_path is None:
        raise typer.BadParameter("--query and --documents-path are required")
    _run_cli(query, documents_path, top_k)


@app.command()
def run(
    query: str = typer.Option(..., help="Query to rerank against"),
    documents_path: Path = typer.Option(..., exists=True, dir_okay=False, file_okay=True),
    top_k: int = typer.Option(5, min=1, max=50),
) -> None:
    _run_cli(query, documents_path, top_k)


if __name__ == "__main__":  # pragma: no cover
    app()

