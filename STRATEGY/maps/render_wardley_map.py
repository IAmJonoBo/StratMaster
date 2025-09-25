#!/usr/bin/env python3
"""Render Wardley maps from the service catalog definition."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml

from stratmaster_orchestrator.decision_support.strategy import WardleyMap, mermaid_diagram


def _load_document(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        if path.suffix.lower() in {".yaml", ".yml"}:
            return yaml.safe_load(handle)
        return json.load(handle)


def main() -> None:
    parser = argparse.ArgumentParser(description="Render Wardley map diagram")
    parser.add_argument("source", type=Path, help="Path to the service catalog definition")
    parser.add_argument("--output", type=Path, default=None, help="Optional output markdown file")
    args = parser.parse_args()

    data = _load_document(args.source)
    wardley_map = WardleyMap.from_dict(data)
    diagram = mermaid_diagram(wardley_map)

    if args.output:
        args.output.write_text(diagram, encoding="utf-8")
    else:
        print(diagram)


if __name__ == "__main__":
    main()
