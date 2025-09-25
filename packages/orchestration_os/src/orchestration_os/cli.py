"""Command-line interface for the StratMaster Orchestration & Decision OS."""
from __future__ import annotations

import argparse
from typing import Sequence

from stratmaster_orchestrator.decision_support import cli as decision_cli


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="strat-orchestrate",
        description="StratMaster orchestration workflows (debate, planning, strategy, governance)",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    decision_cli.register_ach_commands(subparsers)
    decision_cli.register_premortem_commands(subparsers)
    decision_cli.register_bundle_command(subparsers)

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
