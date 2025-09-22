"""Indexer utilities for building a lightweight ColBERT index."""

from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

from .config import ColbertConfig

_TOKEN_PATTERN = re.compile(r"[A-Za-z0-9]+")


def _tokenise(text: str) -> list[str]:
    return [token.lower() for token in _TOKEN_PATTERN.findall(text)]


@dataclass(slots=True)
class IndexedDocument:
    doc_id: str
    text: str
    vector: list[float]


@dataclass(slots=True)
class ColbertIndex:
    name: str
    dim: int
    documents: list[IndexedDocument]

    def save(self, path: Path) -> Path:
        path.mkdir(parents=True, exist_ok=True)
        payload = {
            "name": self.name,
            "dim": self.dim,
            "documents": [
                {"doc_id": doc.doc_id, "text": doc.text, "vector": doc.vector}
                for doc in self.documents
            ],
        }
        index_path = path / "index.json"
        index_path.write_text(json.dumps(payload), encoding="utf-8")
        return index_path

    @classmethod
    def load(cls, path: Path) -> "ColbertIndex":
        data = json.loads(path.read_text(encoding="utf-8"))
        return cls(
            name=data["name"],
            dim=data["dim"],
            documents=[
                IndexedDocument(
                    doc_id=item["doc_id"],
                    text=item["text"],
                    vector=list(map(float, item["vector"])),
                )
                for item in data["documents"]
            ],
        )


class ColbertIndexer:
    def __init__(self, config: ColbertConfig) -> None:
        self.config = config

    def build(self) -> ColbertIndex:
        records = list(self._load_corpus())
        if not records:
            raise ValueError("Corpus yielded no documents")
        documents = [
            IndexedDocument(doc_id=doc_id, text=text, vector=self._embed(text))
            for doc_id, text in records
        ]
        return ColbertIndex(
            name=self.config.index.name,
            dim=self.config.embedding.dim,
            documents=documents,
        )

    def materialise(self, output_dir: Path | None = None) -> Path:
        index = self.build()
        base_path = output_dir or self.config.storage.output_dir / self.config.index.name
        return index.save(Path(base_path))

    def _load_corpus(self) -> Iterable[tuple[str, str]]:
        raw = json.loads(self.config.corpus.path.read_text(encoding="utf-8"))
        collected: list[tuple[str, str]] = []
        self._walk(raw, collected)
        return collected

    def _walk(self, node: object, collected: list[tuple[str, str]]) -> None:
        if isinstance(node, dict):
            if "id" in node:
                text = " ".join(str(node.get(field, "")) for field in self.config.corpus.text_fields)
                if text.strip():
                    collected.append((str(node["id"]), text.strip()))
            for value in node.values():
                self._walk(value, collected)
        elif isinstance(node, list):
            for item in node:
                self._walk(item, collected)

    def _embed(self, text: str) -> list[float]:
        dim = self.config.embedding.dim
        vector = [0.0] * dim
        tokens = _tokenise(text)
        for token in tokens:
            bucket = hash(token) % dim
            vector[bucket] += 1.0
        magnitude = math.sqrt(sum(val * val for val in vector)) or 1.0
        return [val / magnitude for val in vector]


def score(query_vector: Sequence[float], document_vector: Sequence[float]) -> float:
    return float(sum(q * d for q, d in zip(query_vector, document_vector)))


def embed_query(text: str, dim: int) -> list[float]:
    tokens = _tokenise(text)
    vector = [0.0] * dim
    for token in tokens:
        bucket = hash(token) % dim
        vector[bucket] += 1.0
    magnitude = math.sqrt(sum(val * val for val in vector)) or 1.0
    return [val / magnitude for val in vector]

