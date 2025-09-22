"""CLI for building a ColBERT index."""

from __future__ import annotations

from pathlib import Path

import typer

from .config import ColbertConfig, load_config
from .indexer import ColbertIndexer

app = typer.Typer(help="Build and persist a lightweight ColBERT index")


def _build_index(config: Path, output: Path | None) -> None:
    cfg: ColbertConfig = load_config(config)
    indexer = ColbertIndexer(cfg)
    output_path = indexer.materialise(output_dir=output)
    typer.echo(f"Index written to {output_path}")


@app.callback()
def main(
    ctx: typer.Context,
    config: Path = typer.Option(None, exists=True, readable=True),
    output: Path | None = None,
) -> None:
    if ctx.invoked_subcommand is not None:
        return
    if config is None:
        raise typer.BadParameter("--config is required when no subcommand is provided")
    _build_index(config, output)


@app.command()
def build(config: Path = typer.Option(..., exists=True, readable=True), output: Path | None = None) -> None:
    """Build an index using the provided YAML configuration."""

    _build_index(config, output)


if __name__ == "__main__":  # pragma: no cover
    app()

