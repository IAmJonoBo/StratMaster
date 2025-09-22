"""Index SPLADE expansions to a filesystem-backed store."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from .config import SpladeConfig
from .expander import ExpansionRecord, SpladeExpander


@dataclass(slots=True)
class SpladeIndex:
    name: str
    documents: list[ExpansionRecord]

    def save(self, path: Path) -> Path:
        path.mkdir(parents=True, exist_ok=True)
        payload = {
            "name": self.name,
            "documents": [
                {"doc_id": record.doc_id, "expansion": record.expansion}
                for record in self.documents
            ],
        }
        output = path / "index.json"
        output.write_text(json.dumps(payload), encoding="utf-8")
        return output

    @classmethod
    def load(cls, path: Path) -> SpladeIndex:
        data = json.loads(path.read_text(encoding="utf-8"))
        return cls(
            name=data["name"],
            documents=[
                ExpansionRecord(doc_id=item["doc_id"], expansion=item["expansion"])
                for item in data["documents"]
            ],
        )


class SpladeIndexer:
    def __init__(self, config: SpladeConfig) -> None:
        self.config = config

    def build(self) -> SpladeIndex:
        expander = SpladeExpander(self.config)
        records = expander.expand()
        return SpladeIndex(name=self.config.index.name, documents=records)

    def materialise(self, output_dir: Path | None = None) -> Path:
        index = self.build()
        base = output_dir or self.config.storage.output_dir / self.config.index.name
        return index.save(Path(base))
