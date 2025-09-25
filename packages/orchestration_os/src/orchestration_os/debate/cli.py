"""CLI registration helpers for debate workflows."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .ach import ACHMatrix, export_yaml, save_result, update_board
from .premortem import PreMortemScenario, save_markdown

ACH_TEMPLATE = {
    "title": "Feature Launch Readiness",
    "context": "Evaluate whether the upcoming launch is ready for public release",
    "hypotheses": [
        {"id": "H1", "statement": "The feature is ready for global launch"},
        {"id": "H2", "statement": "The feature requires extended beta"},
        {"id": "H3", "statement": "The feature should be cancelled"},
    ],
    "evidence": [
        {
            "id": "E1",
            "description": "Performance tests show p95 latency under target",
            "assessments": {"H1": "support", "H2": "contradict", "H3": "contradict"},
            "weight": 1.0,
        }
    ],
    "decision": {"verdict": "undecided", "rationale": "Pending additional evidence"},
    "actions": [
        {"owner": "release@stratmaster.io", "description": "Collect canary results", "due_date": "2025-01-31"}
    ],
}

PREMORTEM_TEMPLATE = {
    "initiative": "Feature Launch Readiness",
    "time_horizon": "30 days post launch",
    "success_definition": "95% customer satisfaction and <1% incident rate",
    "catastrophe": "Critical reliability incident forces rollback",
    "risk_triggers": [
        "Spike in latency > 300ms",
        "Pager load > 3 incidents per week",
        "Negative sentiment from top 5 enterprise customers",
    ],
    "mitigations": [
        {"risk": "latency", "action": "Auto-scale to 3x capacity", "owner": "platform@stratmaster.io"}
    ],
    "confidence_score": 0.6,
}


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
