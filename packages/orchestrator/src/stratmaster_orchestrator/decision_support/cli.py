"""CLI registration helpers for orchestration decision-support workflows."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .ach import ACHMatrix, export_yaml, save_result, update_board
from .pipeline import DecisionSupportBundle, run_decision_workflow
from .premortem import PreMortemScenario, save_markdown
from .templates import ACH_TEMPLATE, PREMORTEM_TEMPLATE


# --- ACH --------------------------------------------------------------------


def register_ach_commands(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    parser = subparsers.add_parser("ach", help="Run Analysis of Competing Hypotheses workflows")
    parser.set_defaults(handler=_handle_ach)
    parser.add_argument("action", choices=["init-template", "evaluate"], help="ACH action to run")
    parser.add_argument("--path", type=Path, default=None, help="Template output path when init-template is used")
    parser.add_argument("--input", type=Path, default=None, help="ACH definition to evaluate (JSON)")
    parser.add_argument("--output", type=Path, default=None, help="Where to write the machine-readable verdict")
    parser.add_argument("--board", type=Path, default=None, help="Decision board markdown path to update")
    parser.add_argument(
        "--critique",
        choices=["light", "standard", "strict"],
        default="standard",
        help="Critique intensity level",
    )
    parser.add_argument(
        "--export-yaml",
        type=Path,
        default=None,
        help="Optional path to export the evaluated matrix as YAML",
    )


def _handle_ach(args: argparse.Namespace) -> int:
    if args.action == "init-template":
        if not args.path:
            raise SystemExit("--path is required when using init-template")
        args.path.parent.mkdir(parents=True, exist_ok=True)
        args.path.write_text(json.dumps(ACH_TEMPLATE, indent=2), encoding="utf-8")
        return 0

    if not args.input:
        raise SystemExit("--input is required for ACH evaluation")

    payload = json.loads(args.input.read_text(encoding="utf-8"))
    matrix = ACHMatrix.from_dict(payload)
    matrix.evaluate(critique_level=args.critique)

    if args.output:
        save_result(args.output, matrix)
    else:
        print(json.dumps(matrix.to_dict(), indent=2))
    if args.export_yaml:
        export_yaml(args.export_yaml, matrix)
    if args.board:
        update_board(args.board, matrix)
    if matrix.critiques or matrix.consistency_warnings:
        issues = matrix.critiques + matrix.consistency_warnings
        print("Warnings detected:\n- " + "\n- ".join(issues))
        return 2
    return 0


# --- Pre-mortem -------------------------------------------------------------


def register_premortem_commands(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> None:
    parser = subparsers.add_parser("premortem", help="Run pre-mortem workshops")
    parser.set_defaults(handler=_handle_premortem)
    parser.add_argument("action", choices=["init-template", "run"], help="Pre-mortem action to run")
    parser.add_argument("--path", type=Path, default=None, help="Output path for init-template")
    parser.add_argument("--input", type=Path, default=None, help="Pre-mortem scenario definition (JSON)")
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Where to write the generated markdown report (run action)",
    )


def _handle_premortem(args: argparse.Namespace) -> int:
    if args.action == "init-template":
        if not args.path:
            raise SystemExit("--path is required when using init-template")
        args.path.parent.mkdir(parents=True, exist_ok=True)
        args.path.write_text(json.dumps(PREMORTEM_TEMPLATE, indent=2), encoding="utf-8")
        return 0

    if not args.input:
        raise SystemExit("--input is required for pre-mortem run")

    payload = json.loads(args.input.read_text(encoding="utf-8"))
    scenario = PreMortemScenario.from_dict(payload)
    if args.output:
        save_markdown(args.output, scenario)
    else:
        print(scenario.render_markdown())
    return 0


# --- Decision bundle --------------------------------------------------------


def register_bundle_command(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    parser = subparsers.add_parser("bundle", help="Run orchestrator, ACH, and pre-mortem together")
    parser.set_defaults(handler=_handle_bundle)
    parser.add_argument("--query", required=True, help="Primary orchestration query")
    parser.add_argument("--tenant", default="strategy-ops", help="Tenant identifier for orchestration state")
    parser.add_argument(
        "--ach-input",
        type=Path,
        default=Path("DECISIONS/ach_inputs/sample_ach.json"),
        help="ACH definition to evaluate",
    )
    parser.add_argument(
        "--premortem-input",
        type=Path,
        default=Path("DECISIONS/premortems/feature_launch.json"),
        help="Pre-mortem scenario to load",
    )
    parser.add_argument("--board", type=Path, default=Path("DECISIONS/ACH_BOARD.md"), help="Decision board to update")
    parser.add_argument(
        "--ach-output",
        type=Path,
        default=Path("DECISIONS/ach_results/bundle.json"),
        help="Where to write the ACH evaluation JSON",
    )
    parser.add_argument(
        "--export-yaml",
        type=Path,
        default=Path("DECISIONS/ach_results/bundle.yaml"),
        help="Optional path to export the evaluated ACH as YAML",
    )
    parser.add_argument(
        "--premortem-markdown",
        type=Path,
        default=Path("DECISIONS/premortems/bundle.md"),
        help="Where to write the generated pre-mortem markdown",
    )
    parser.add_argument(
        "--planning-backlog",
        type=Path,
        default=Path("orchestration/planning/planning_backlog.yaml"),
        help="Backlog used for planning summaries",
    )
    parser.add_argument(
        "--wardley-map",
        type=Path,
        default=Path("STRATEGY/maps/service_catalog.yaml"),
        help="Wardley map YAML to render",
    )
    parser.add_argument(
        "--huggingface-model",
        default=None,
        help="Optional HuggingFace model for additional critiques",
    )
    parser.add_argument(
        "--critique",
        choices=["light", "standard", "strict"],
        default="standard",
        help="ACH critique level",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("DECISIONS/ach_results/bundle_summary.json"),
        help="Where to write the aggregated decision-support bundle",
    )


def _handle_bundle(args: argparse.Namespace) -> int:
    bundle = run_decision_workflow(
        query=args.query,
        tenant_id=args.tenant,
        ach_path=args.ach_input,
        premortem_path=args.premortem_input,
        critique_level=args.critique,
        board_path=args.board,
        ach_output_path=args.ach_output,
        ach_yaml_export=args.export_yaml,
        premortem_markdown=args.premortem_markdown,
        planning_backlog_path=args.planning_backlog,
        wardley_map_path=args.wardley_map,
        huggingface_model=args.huggingface_model,
    )
    payload = bundle.to_dict()
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    else:
        print(json.dumps(payload, indent=2))
    for warning in bundle.warnings:
        print(f"Warning: {warning}")
    for error in bundle.errors:
        print(f"Error: {error}")
    return 2 if bundle.errors else 0


__all__ = [
    "DecisionSupportBundle",
    "register_ach_commands",
    "register_bundle_command",
    "register_premortem_commands",
]
