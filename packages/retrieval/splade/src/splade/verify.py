"""Verify SPLADE expansions against stored index."""

from __future__ import annotations

import json
from pathlib import Path

import typer

from .config import load_config
from .indexer import SpladeIndex

app = typer.Typer(help="Verify SPLADE expansions align with the index")


def _run_verify(config: Path, index_path: Path, expansions_path: Path) -> None:
    load_config(config)  # validate config structure
    index = SpladeIndex.load(index_path)
    expansions = {
        item["doc_id"]: item["expansion"]
        for item in (
            json.loads(line)
            for line in expansions_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        )
    }
    missing = [doc.doc_id for doc in index.documents if doc.doc_id not in expansions]
    if missing:
        raise typer.Exit(code=1)
    typer.echo("All expansions present in index")


@app.callback()
def main(
    ctx: typer.Context,
    config: Path = typer.Option(None, exists=True, readable=True),
    index_path: Path = typer.Option(None, exists=True, dir_okay=False, file_okay=True),
    expansions_path: Path = typer.Option(
        None, exists=True, dir_okay=False, file_okay=True
    ),
) -> None:
    if ctx.invoked_subcommand is not None:
        return
    if None in (config, index_path, expansions_path):
        raise typer.BadParameter(
            "--config, --index-path, and --expansions-path are required"
        )
    _run_verify(config, index_path, expansions_path)


@app.command()
def run(
    config: Path = typer.Option(..., exists=True, readable=True),
    index_path: Path = typer.Option(..., exists=True, dir_okay=False, file_okay=True),
    expansions_path: Path = typer.Option(
        ..., exists=True, dir_okay=False, file_okay=True
    ),
) -> None:
    _run_verify(config, index_path, expansions_path)


if __name__ == "__main__":  # pragma: no cover
    app()
