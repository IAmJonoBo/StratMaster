"""Generate SPLADE-style sparse expansions."""

from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from pathlib import Path

from .config import SpladeConfig

_TOKEN_PATTERN = re.compile(r"[A-Za-z0-9]+")


def _tokenise(text: str) -> list[str]:
    return [token.lower() for token in _TOKEN_PATTERN.findall(text)]


@dataclass(slots=True)
class ExpansionRecord:
    doc_id: str
    expansion: dict[str, float]


class SpladeExpander:
    def __init__(self, config: SpladeConfig, max_features: int = 200) -> None:
        self.config = config
        self.max_features = max_features

    def expand(self) -> list[ExpansionRecord]:
        raw = json.loads(self.config.corpus.path.read_text(encoding="utf-8"))
        records: list[ExpansionRecord] = []
        self._walk(raw, records)
        return records

    def _walk(self, node: object, records: list[ExpansionRecord]) -> None:
        if isinstance(node, dict):
            if "id" in node:
                text = " ".join(
                    str(node.get(field, "")) for field in self.config.corpus.text_fields
                )
                weights = self._expand_text(text)
                if weights:
                    records.append(
                        ExpansionRecord(doc_id=str(node["id"]), expansion=weights)
                    )
            for value in node.values():
                self._walk(value, records)
        elif isinstance(node, list):
            for item in node:
                self._walk(item, records)

    def _expand_text(self, text: str) -> dict[str, float]:
        tokens = _tokenise(text)
        if not tokens:
            return {}
        counts: dict[str, int] = {}
        for token in tokens:
            counts[token] = counts.get(token, 0) + 1
        norm = math.sqrt(sum(val * val for val in counts.values())) or 1.0
        weighted = {token: round(count / norm, 4) for token, count in counts.items()}
        sorted_items = sorted(weighted.items(), key=lambda item: item[1], reverse=True)
        return dict(sorted_items[: self.max_features])

    def write(self, output_path: Path) -> Path:
        records = self.expand()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", encoding="utf-8") as fh:
            for record in records:
                fh.write(
                    json.dumps({"doc_id": record.doc_id, "expansion": record.expansion})
                )
                fh.write("\n")
        return output_path
