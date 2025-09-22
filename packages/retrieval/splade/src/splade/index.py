"""CLI for indexing SPLADE expansions."""

from __future__ import annotations

from pathlib import Path

import typer

from .config import load_config
from .indexer import SpladeIndexer

app = typer.Typer(help="Index SPLADE expansions into a JSON store")


def _build_index(config: Path, output: Path | None) -> None:
    cfg = load_config(config)
    indexer = SpladeIndexer(cfg)
    output_path = indexer.materialise(output_dir=output)
    typer.echo(f"SPLADE index written to {output_path}")


@app.callback()
def main(
    ctx: typer.Context,
    config: Path = typer.Option(None, exists=True, readable=True),
    output: Path | None = typer.Option(None),
) -> None:
    if ctx.invoked_subcommand is not None:
        return
    if config is None:
        raise typer.BadParameter("--config is required")
    _build_index(config, output)


@app.command()
def build(
    config: Path = typer.Option(..., exists=True, readable=True),
    output: Path | None = typer.Option(None),
) -> None:
    _build_index(config, output)


if __name__ == "__main__":  # pragma: no cover
    app()
