"""CLI to generate SPLADE expansions."""

from __future__ import annotations

from pathlib import Path

import typer

from .config import load_config
from .expander import SpladeExpander

app = typer.Typer(help="Generate sparse expansions for SPLADE indexing")


def _run_expand(config: Path, output: Path, max_features: int) -> None:
    cfg = load_config(config)
    expander = SpladeExpander(cfg, max_features=max_features)
    output_path = expander.write(output)
    typer.echo(f"Expansions written to {output_path}")


@app.callback()
def main(
    ctx: typer.Context,
    config: Path = typer.Option(None, exists=True, readable=True),
    output: Path = typer.Option(Path("artifacts/splade/expansions.jsonl")),
    max_features: int = typer.Option(200, min=10, max=1000),
) -> None:
    if ctx.invoked_subcommand is not None:
        return
    if config is None:
        raise typer.BadParameter("--config is required")
    _run_expand(config, output, max_features)


@app.command()
def run(
    config: Path = typer.Option(..., exists=True, readable=True),
    output: Path = typer.Option(Path("artifacts/splade/expansions.jsonl")),
    max_features: int = typer.Option(200, min=10, max=1000),
) -> None:
    _run_expand(config, output, max_features)


if __name__ == "__main__":  # pragma: no cover
    app()

