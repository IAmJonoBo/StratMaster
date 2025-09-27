"""StratMaster V2 Feature Flags

Lightweight loader for runtime feature toggles. Flags are sourced in this order:
1. Environment variable override (e.g. ENABLE_COLLAB_LIVE=1)
2. Local JSON file: configs/v2-flags.json (developer / env specific)
3. Example defaults: configs/v2-flags.example.json (repository baseline)

Environment variables accept truthy values: '1','true','yes','on'.

Usage:
    from stratmaster_api.feature_flags import flags
    if flags.collab_live:
        ...

Add new flags by extending FlagDefaults and updating the mapping.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

_TRUTHY = {"1", "true", "yes", "on"}

CONFIG_DIR = Path(__file__).resolve().parents[4] / "configs"
PRIMARY_FILE = CONFIG_DIR / "v2-flags.json"
EXAMPLE_FILE = CONFIG_DIR / "v2-flags.example.json"

@dataclass(frozen=True)
class FlagState:
    collab_live: bool
    model_recommender_v2: bool
    predictive_analytics: bool
    event_streaming: bool
    industry_templates: bool

    def as_dict(self) -> dict[str, bool]:  # convenience for diagnostics
        return {
            "ENABLE_COLLAB_LIVE": self.collab_live,
            "ENABLE_MODEL_RECOMMENDER_V2": self.model_recommender_v2,
            "ENABLE_PREDICTIVE_ANALYTICS": self.predictive_analytics,
            "ENABLE_EVENT_STREAMING": self.event_streaming,
            "ENABLE_INDUSTRY_TEMPLATES": self.industry_templates,
        }

_DEFAULTS = {
    "ENABLE_COLLAB_LIVE": False,
    "ENABLE_MODEL_RECOMMENDER_V2": True,
    "ENABLE_PREDICTIVE_ANALYTICS": False,
    "ENABLE_EVENT_STREAMING": False,
    "ENABLE_INDUSTRY_TEMPLATES": False,
}


def _load_file(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:  # pragma: no cover - defensive
        return {}


def _coerce_bool(val: Any) -> bool:
    if isinstance(val, bool):
        return val
    if isinstance(val, str):
        return val.lower() in _TRUTHY
    if isinstance(val, (int, float)):
        return bool(val)
    return False


def _merge_sources() -> dict[str, bool]:
    # Start with defaults
    merged: dict[str, bool] = {k: bool(v) for k, v in _DEFAULTS.items()}

    # Overlay example file (acts as documented baseline if changed)
    for k, v in _load_file(EXAMPLE_FILE).items():
        if k in merged:
            merged[k] = _coerce_bool(v)

    # Overlay primary file (developer / environment specific)
    for k, v in _load_file(PRIMARY_FILE).items():
        if k in merged:
            merged[k] = _coerce_bool(v)

    # Finally environment variables
    for k in merged.keys():
        env_val = os.getenv(k)
        if env_val is not None:
            merged[k] = _coerce_bool(env_val)

    return merged


def _build_state(data: dict[str, bool]) -> FlagState:
    return FlagState(
        collab_live=data["ENABLE_COLLAB_LIVE"],
        model_recommender_v2=data["ENABLE_MODEL_RECOMMENDER_V2"],
        predictive_analytics=data["ENABLE_PREDICTIVE_ANALYTICS"],
        event_streaming=data["ENABLE_EVENT_STREAMING"],
        industry_templates=data["ENABLE_INDUSTRY_TEMPLATES"],
    )


# Public singleton state
flags = _build_state(_merge_sources())


def reload_flags() -> FlagState:
    """Reload flags from disk/env (useful in dev hot-reload)."""
    global flags  # type: ignore
    flags = _build_state(_merge_sources())
    return flags

__all__ = ["flags", "reload_flags", "FlagState"]
