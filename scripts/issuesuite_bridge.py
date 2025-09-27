#!/usr/bin/env python3
"""High-level wrapper around the external IssueSuite CLI.

The StratMaster SCRATCH.md plan calls for integrated issue automation backed by
https://github.com/IAmJonoBo/IssueSuite.  The repository already documents the
CLI commands but automation (CI jobs, agents, remote runners) need a stable
Python surface so they can run validations, dry-run syncs and schema exports
without duplicating shell pipelines.  This module provides that bridge.

The wrapper prefers the `issuesuite` CLI (`python -m issuesuite.cli ...`) so it
works even when the Python package does not expose a public API.  Commands are
run with mock-mode disabled by default but callers may enable it when operating
without GitHub credentials.

Example:
    from issuesuite_bridge import IssueSuiteBridge
    bridge = IssueSuiteBridge(mock_mode=True)
    result = bridge.validate(skip_label_exists=True)
    if result.ok:
        print("config valid")
    else:
        print(result.stderr)
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable, Mapping, Sequence

CommandRunner = Callable[[Sequence[str], Mapping[str, str]], subprocess.CompletedProcess[str]]


@dataclass(slots=True)
class CommandResult:
    """Captured output from an IssueSuite command."""

    command: list[str]
    stdout: str
    stderr: str
    returncode: int

    @property
    def ok(self) -> bool:
        return self.returncode == 0

    def raise_for_status(self) -> None:
        if not self.ok:
            raise RuntimeError(
                f"IssueSuite command failed ({self.returncode}): {' '.join(self.command)}\n"
                f"stdout:\n{self.stdout}\n"
                f"stderr:\n{self.stderr}"
            )


class IssueSuiteBridge:
    """Wrapper to invoke IssueSuite operations from Python."""

    def __init__(
        self,
        config_path: str | os.PathLike[str] = "issue_suite.config.yaml",
        *,
        python_executable: str | None = None,
        env: Mapping[str, str] | None = None,
        mock_mode: bool | None = None,
        runner: CommandRunner | None = None,
    ) -> None:
        self.config_path = Path(config_path)
        if not self.config_path.exists():
            raise FileNotFoundError(f"IssueSuite config not found: {self.config_path}")

        self.python_executable = python_executable or sys.executable
        self._env = os.environ.copy()
        if env:
            self._env.update(env)
        if mock_mode is not None:
            self._env["ISSUES_SUITE_MOCK"] = "1" if mock_mode else "0"

        self._runner = runner or self._default_runner

    # ------------------------------------------------------------------
    # Introspection helpers
    # ------------------------------------------------------------------
    @staticmethod
    def is_installed() -> bool:
        """Return True when the issuesuite module can be imported."""

        try:
            __import__("issuesuite")
            return True
        except Exception:  # pragma: no cover - import failure path
            return False

    # ------------------------------------------------------------------
    # Public operations
    # ------------------------------------------------------------------
    def validate(
        self,
        *,
        strict: bool = False,
        skip_label_exists: bool = False,
        skip_milestone_exists: bool = False,
    ) -> CommandResult:
        """Run IssueSuite validation."""

        args: list[str] = ["--config", str(self.config_path)]
        if strict:
            args.append("--strict")
        if skip_label_exists:
            args.append("--skip-label-exists")
        if skip_milestone_exists:
            args.append("--skip-milestone-exists")
        return self._run_cli("validate", args)

    def summary(self, *, output_path: str | os.PathLike[str] | None = None) -> CommandResult:
        """Generate a human readable summary."""

        args: list[str] = ["--config", str(self.config_path)]
        if output_path:
            args.extend(["--output", str(output_path)])
        return self._run_cli("summary", args)

    def sync(
        self,
        *,
        dry_run: bool = True,
        update: bool = True,
        summary_json: str | os.PathLike[str] | None = None,
    ) -> CommandResult:
        """Execute the sync command, defaulting to a dry-run."""

        args: list[str] = ["--config", str(self.config_path)]
        if dry_run:
            args.append("--dry-run")
        if update:
            args.append("--update")
        if summary_json:
            args.extend(["--summary-json", str(summary_json)])
        return self._run_cli("sync", args)

    def export(
        self,
        *,
        pretty: bool = False,
        output: str | os.PathLike[str] | None = None,
    ) -> CommandResult:
        """Export issues into a machine readable JSON document."""

        args: list[str] = ["--config", str(self.config_path)]
        if pretty:
            args.append("--pretty")
        if output:
            args.extend(["--output", str(output)])
        return self._run_cli("export", args)

    def schema(self, *, summary: bool = False) -> CommandResult:
        """Export IssueSuite JSON Schemas for automation consumers."""

        args = ["--config", str(self.config_path)]
        if summary:
            args.append("--summary")
        return self._run_cli("schema", args)

    # ------------------------------------------------------------------
    # Convenience helpers
    # ------------------------------------------------------------------
    def dry_run_report(self) -> dict[str, object]:
        """Run validation + summary and return structured info."""

        validate_result = self.validate(skip_label_exists=True, skip_milestone_exists=True)
        summary_result = self.summary()

        report = {
            "validate_ok": validate_result.ok,
            "summary_ok": summary_result.ok,
            "validate_stdout": validate_result.stdout,
            "summary_stdout": summary_result.stdout,
        }

        summary_json_path = Path("issues_summary.json")
        if summary_json_path.exists():
            try:
                report["summary_json"] = json.loads(summary_json_path.read_text())
            except json.JSONDecodeError:  # pragma: no cover - depends on CLI output
                report["summary_json"] = None
        return report

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _run_cli(self, subcommand: str, args: Iterable[str]) -> CommandResult:
        if not self.is_installed():
            raise RuntimeError(
                "issuesuite is not installed. Run `make issuesuite.install` or set "
                "ISSUESUITE_TARBALL before invoking IssueSuiteBridge."
            )

        cmd = [self.python_executable, "-m", "issuesuite.cli", subcommand]
        cmd.extend(args)
        result = self._runner(cmd, self._env)
        return CommandResult(cmd, result.stdout, result.stderr, result.returncode)

    @staticmethod
    def _default_runner(cmd: Sequence[str], env: Mapping[str, str]) -> subprocess.CompletedProcess[str]:
        return subprocess.run(cmd, capture_output=True, text=True, env=env, check=False)


def main(argv: Sequence[str] | None = None) -> int:
    """Small CLI exposing a few high-level commands."""

    import argparse

    parser = argparse.ArgumentParser(description="IssueSuite integration helper")
    parser.add_argument("command", choices=["validate", "summary", "sync", "export", "schema", "report"])
    parser.add_argument("--config", default="issue_suite.config.yaml")
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--no-dry-run", action="store_true")
    parser.add_argument("--pretty", action="store_true")
    parser.add_argument("--output")
    parser.add_argument("--summary-json")
    parser.add_argument("--mock", action="store_true")
    parser.add_argument("--summary-schema", action="store_true", dest="summary_schema")

    args = parser.parse_args(argv)
    bridge = IssueSuiteBridge(args.config, mock_mode=args.mock)

    if args.command == "validate":
        result = bridge.validate(strict=args.strict)
    elif args.command == "summary":
        result = bridge.summary(output_path=args.output)
    elif args.command == "sync":
        result = bridge.sync(dry_run=not args.no_dry_run, summary_json=args.summary_json)
    elif args.command == "export":
        result = bridge.export(pretty=args.pretty, output=args.output)
    elif args.command == "schema":
        result = bridge.schema(summary=args.summary_schema)
    else:  # report
        report = bridge.dry_run_report()
        print(json.dumps(report, indent=2))
        return 0

    if result.stdout:
        print(result.stdout.strip())
    if result.stderr:
        print(result.stderr.strip(), file=sys.stderr)
    return result.returncode


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
