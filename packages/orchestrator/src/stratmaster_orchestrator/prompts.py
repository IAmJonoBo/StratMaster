"""Utilities for loading constitutional prompts for agent debate."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class DebatePrompts:
    house: Mapping[str, Any]
    adversary: Mapping[str, Any]
    critic: Mapping[str, Any]


def _load_yaml(path: Path) -> Mapping[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"Prompt file {path} did not contain a mapping")
    return data


def load_prompts(base_dir: Path | None = None) -> DebatePrompts:
    """Load the canonical debate prompts from disk."""

    if base_dir is None:
        base_dir = Path(__file__).resolve().parents[4] / "prompts" / "constitutions"
    house = _load_yaml(base_dir / "house_rules.yaml")
    adversary = _load_yaml(base_dir / "adversary.yaml")
    critic = _load_yaml(base_dir / "critic.yaml")
    return DebatePrompts(house=house, adversary=adversary, critic=critic)
