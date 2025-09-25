"""Wardley mapping helpers embedded in the decision-support suite."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass(slots=True)
class Component:
    name: str
    visibility: float
    stage: str
    owner: str | None = None


@dataclass(slots=True)
class Link:
    source: str
    target: str


@dataclass(slots=True)
class WardleyMap:
    context: str
    components: list[Component]
    links: list[Link]

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> "WardleyMap":
        components = [
            Component(
                name=str(item["component"]),
                visibility=float(item.get("visibility", 0.5)),
                stage=str(item.get("stage", "product")),
                owner=item.get("owner"),
            )
            for item in payload.get("value_chain", [])
        ]
        links = [
            Link(source=str(item.get("from")), target=str(item.get("to")))
            for item in payload.get("links", [])
        ]
        return cls(context=str(payload.get("context", "Wardley Map")), components=components, links=links)


STAGE_COORDINATES = {
    "genesis": 0.1,
    "custom": 0.35,
    "product": 0.65,
    "commodity": 0.9,
}


def load_map(path: Path) -> WardleyMap:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    return WardleyMap.from_dict(payload)


def mermaid_diagram(map_: WardleyMap) -> str:
    lines = ["```mermaid", "graph LR", f"  %% Context: {map_.context}"]
    class_defs: set[str] = set()
    for component in map_.components:
        stage = STAGE_COORDINATES.get(component.stage.lower(), 0.5)
        visibility = max(0.05, min(component.visibility, 1.0))
        node_name = component.name.replace(" ", "_")
        label = f"{component.name} ({component.stage})"
        stage_key = f"stage{int(stage * 10)}"
        lines.append(f"  {node_name}([{label}]):::{stage_key}")
        if stage_key not in class_defs:
            class_defs.add(stage_key)
            intensity = max(20, min(int(stage * 100), 90))
            lines.append(
                f"  classDef {stage_key} fill:#0EA5E9{intensity:02X},stroke:#1F2933,stroke-width:1px;"
            )
        lines.append(f"  %% visibility: {visibility:.2f}")
    for link in map_.links:
        lines.append(
            f"  {link.source.replace(' ', '_')} --> {link.target.replace(' ', '_')}"
        )
    lines.append("```")
    return "\n".join(lines)


__all__ = ["Component", "Link", "WardleyMap", "load_map", "mermaid_diagram"]
