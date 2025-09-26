#!/usr/bin/env python3
"""Validate required milestone titles exist in the GitHub repository.

Exit status:
 0 = all required milestones found
 1 = one or more required milestones missing or API error

Resolution targets:
 - Ensures roadmap / automation scripts (create_github_issues.sh) remain consistent
 - Provides early CI feedback if someone renames or deletes a milestone

Lookup order for fetching milestones:
 1. gh CLI (fast, uses current auth) if available
 2. GitHub REST API via environment token (GITHUB_TOKEN / GH_TOKEN) and repo autodetect

Repository inference:
 - In CI, GITHUB_REPOSITORY is used (format owner/repo)
 - Locally, we attempt to parse `git config --get remote.origin.url`

Usage:
  python scripts/validate_milestones.py                # default required set
  python scripts/validate_milestones.py --list         # print fetched milestones
  python scripts/validate_milestones.py --expected M1:... "Sprint 0: Mobilize & Baseline"

The default required list is derived from v2 roadmap documentation.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from typing import Iterable
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

DEFAULT_REQUIRED = [
    "M1: Real-Time Foundation",
    "M2: Performance & Validation",
    "M3: Advanced Analytics",
    "M4: Enterprise Features",
    "Sprint 0: Mobilize & Baseline",
]


def _debug(msg: str, verbose: bool):
    if verbose:
        print(f"[debug] {msg}")


def infer_repo(verbose: bool) -> tuple[str, str]:
    repo_env = os.getenv("GITHUB_REPOSITORY")
    if repo_env and "/" in repo_env:
        owner, name = repo_env.split("/", 1)
        _debug(f"Using repo from GITHUB_REPOSITORY: {owner}/{name}", verbose)
        return owner, name
    # Fallback: parse git remote URL
    try:
        remote_url = subprocess.check_output(
            ["git", "config", "--get", "remote.origin.url"], text=True
        ).strip()
        # Patterns: git@github.com:owner/repo.git or https://github.com/owner/repo.git
        m = re.search(r"github.com[:/](.+?)/(.+?)(?:\.git)?$", remote_url)
        if m:
            owner, name = m.group(1), m.group(2)
            _debug(f"Parsed repo from remote URL: {owner}/{name}", verbose)
            return owner, name
    except Exception:
        pass
    raise SystemExit("Unable to infer repository (set GITHUB_REPOSITORY)")


def fetch_milestones(owner: str, repo: str, verbose: bool) -> list[str]:
    # 1. Try gh CLI
    try:
        subprocess.check_call(["gh", "auth", "status"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        _debug("Using gh CLI for milestone retrieval", verbose)
        out = subprocess.check_output(
            [
                "gh", "api", f"repos/{owner}/{repo}/milestones", "--method", "GET",
                "-f", "state=all", "-F", "per_page=100",
            ],
            text=True,
        )
        data = json.loads(out)
        return [m["title"] for m in data]
    except Exception:
        _debug("gh CLI unavailable or failed; falling back to REST", verbose)

    # 2. Direct REST API
    token = os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN")
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    else:
        _debug("No token found; unauthenticated request (may be rate limited)", verbose)
    url = f"https://api.github.com/repos/{owner}/{repo}/milestones?state=all&per_page=100"
    try:
        req = Request(url, headers=headers)
        with urlopen(req, timeout=10) as resp:  # nosec B310 - controlled URL
            data = json.loads(resp.read().decode("utf-8"))
            return [m["title"] for m in data]
    except HTTPError as e:
        print(f"Error: HTTP {e.code} while fetching milestones: {e.reason}")
    except URLError as e:
        print(f"Error: Network error while fetching milestones: {e.reason}")
    except Exception as e:
        print(f"Error: Unexpected error fetching milestones: {e}")
    return []


def validate(required: Iterable[str], available: Iterable[str]) -> tuple[list[str], list[str]]:
    available_set = set(available)
    missing = [r for r in required if r not in available_set]
    present = [r for r in required if r in available_set]
    return present, missing


def main():  # noqa: C901 - acceptable small script
    parser = argparse.ArgumentParser(description="Validate required GitHub milestones exist")
    parser.add_argument(
        "--expected",
        nargs="*",
        help="Explicit list of required milestone titles (override defaults)",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="Only list fetched milestones and exit",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose debug logging",
    )
    args = parser.parse_args()

    owner, repo = infer_repo(args.verbose)
    milestones = fetch_milestones(owner, repo, args.verbose)
    if not milestones:
        print("Error: Could not fetch milestones (empty result)")
        sys.exit(1)

    if args.list:
        print("Fetched milestones:")
        for m in milestones:
            print(f" - {m}")
        return

    required = args.expected if args.expected else DEFAULT_REQUIRED
    present, missing = validate(required, milestones)

    print("Milestone Validation Report")
    print(f"Repository: {owner}/{repo}")
    print(f"Total fetched: {len(milestones)}")
    print(f"Required: {len(required)} | Present: {len(present)} | Missing: {len(missing)}")

    if present:
        print("\nPresent milestones:")
        for m in present:
            print(f"  ✅ {m}")
    if missing:
        print("\nMissing milestones:")
        for m in missing:
            print(f"  ❌ {m}")
        print("\n❌ Validation failed")
        sys.exit(1)

    print("\n✅ All required milestones present")


if __name__ == "__main__":  # pragma: no cover
    main()
