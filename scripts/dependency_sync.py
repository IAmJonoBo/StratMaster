#!/usr/bin/env python3
"""Intelligent dependency sync helper for local vs remote environments.

SCRATCH.md calls for dependency management that keeps development and remote
runtimes aligned.  The repo already maintains consolidated requirements and lock
files; this utility layers on top by comparing the *actual* Python environment
(`pip list`) with a recorded remote snapshot (JSON exported from production).

When differences are found the tool prints actionable remediation steps so
engineers can correct drift before deploying.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, Sequence

DEFAULT_REMOTE = Path("configs/dependencies/remote_environment.json")


@dataclass(slots=True)
class PackageDiff:
    missing_local: dict[str, str]
    version_mismatch: dict[str, tuple[str, str]]
    extra_local: dict[str, str]

    def is_clean(self) -> bool:
        return not (self.missing_local or self.version_mismatch or self.extra_local)


def load_remote_packages(path: Path) -> dict[str, str]:
    data = json.loads(path.read_text())
    packages = {entry["name"].lower(): entry["version"] for entry in data.get("packages", [])}
    return packages


def load_local_packages(freeze_path: Path | None) -> dict[str, str]:
    if freeze_path is not None:
        return parse_freeze_lines(freeze_path.read_text().splitlines())

    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "list", "--format", "json"],
            capture_output=True,
            text=True,
            check=True,
        )
    except Exception as exc:  # pragma: no cover - depends on runtime environment
        raise RuntimeError(f"Unable to inspect local environment: {exc}") from exc

    packages = json.loads(result.stdout)
    return {entry["name"].lower(): entry["version"] for entry in packages}


def parse_freeze_lines(lines: Iterable[str]) -> dict[str, str]:
    packages: dict[str, str] = {}
    for raw in lines:
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "==" in line:
            name, version = line.split("==", 1)
            packages[name.lower()] = version
    return packages


def diff_packages(local: Dict[str, str], remote: Dict[str, str]) -> PackageDiff:
    missing_local: dict[str, str] = {}
    version_mismatch: dict[str, tuple[str, str]] = {}
    extra_local: dict[str, str] = {}

    for name, version in remote.items():
        if name not in local:
            missing_local[name] = version
        elif local[name] != version:
            version_mismatch[name] = (local[name], version)

    for name, version in local.items():
        if name not in remote:
            extra_local[name] = version

    return PackageDiff(missing_local, version_mismatch, extra_local)


def print_report(diff: PackageDiff) -> None:
    if diff.is_clean():
        print("✅ Local environment matches remote snapshot")
        return

    if diff.missing_local:
        print("❌ Packages missing locally:")
        for name, version in sorted(diff.missing_local.items()):
            print(f"  - {name}=={version}")

    if diff.version_mismatch:
        print("⚠️ Version drift detected:")
        for name, (local_ver, remote_ver) in sorted(diff.version_mismatch.items()):
            print(f"  - {name}: local {local_ver} -> remote {remote_ver}")

    if diff.extra_local:
        print("ℹ️ Extra local packages (not present remotely):")
        for name, version in sorted(diff.extra_local.items()):
            print(f"  - {name}=={version}")

    print("\nSuggested actions:")
    if diff.missing_local or diff.version_mismatch:
        pins = [
            f"{name}=={remote_ver if isinstance(remote_ver, str) else remote_ver[1]}"
            for name, remote_ver in [
                *(diff.missing_local.items()),
                *((name, remote) for name, (_, remote) in diff.version_mismatch.items()),
            ]
        ]
        cmd = " ".join(pins)
        print(f"  pip install {cmd}")
    if diff.extra_local:
        extras = " ".join(diff.extra_local)
        print(f"  pip uninstall {extras}")


def run(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Compare local packages with remote snapshot")
    parser.add_argument("command", choices=["status", "sync"], nargs="?", default="status")
    parser.add_argument("--remote", type=Path, default=DEFAULT_REMOTE, help="Path to remote JSON snapshot")
    parser.add_argument("--freeze", type=Path, help="Optional pip freeze file to treat as local")
    parser.add_argument("--json", action="store_true", help="Emit machine readable diff")
    args = parser.parse_args(argv)

    if not args.remote.exists():
        raise SystemExit(f"Remote snapshot not found: {args.remote}")

    remote_packages = load_remote_packages(args.remote)
    local_packages = load_local_packages(args.freeze)
    diff = diff_packages(local_packages, remote_packages)

    if args.json:
        payload = {
            "missing_local": diff.missing_local,
            "version_mismatch": {
                name: {"local": local, "remote": remote}
                for name, (local, remote) in diff.version_mismatch.items()
            },
            "extra_local": diff.extra_local,
            "clean": diff.is_clean(),
        }
        print(json.dumps(payload, indent=2))
    else:
        print_report(diff)

    if args.command == "sync" and not diff.is_clean():
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(run())
