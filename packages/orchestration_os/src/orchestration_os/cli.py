"""Command-line interface for the StratMaster Orchestration & Decision OS."""
from __future__ import annotations

import argparse
from typing import Sequence

from .debate import cli as debate_cli


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="strat-orchestrate",
        description="StratMaster orchestration workflows (debate, planning, strategy, governance)",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    debate_cli.register_ach_commands(subparsers)
    debate_cli.register_premortem_commands(subparsers)

    return parser


def app_main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    handler = getattr(args, "handler", None)
    if handler is None:
        parser.print_help()
        return 1
    return handler(args)


if __name__ == "__main__":  # pragma: no cover - manual execution
    raise SystemExit(app_main())
