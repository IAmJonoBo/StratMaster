"""In-process repositories backing the knowledge fabric."""

from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Mapping

from .contracts import ArtefactRecord, RankedArtefact, TenantManifest


class VectorStore:
    """Tenant aware dense vector store backed by JSON serialisation."""

    def __init__(self, base_path: Path | str | None = None) -> None:
        self._base_path = Path(base_path or "artifacts/knowledge/vectors")
        self._base_path.mkdir(parents=True, exist_ok=True)
        self._records: dict[str, list[ArtefactRecord]] = defaultdict(list)
        self._load_from_disk()

    def upsert(self, artefacts: Iterable[ArtefactRecord]) -> None:
        for artefact in artefacts:
            records = self._records[artefact.tenant_id]
            filtered = [rec for rec in records if rec.document_id != artefact.document_id]
            filtered.append(artefact)
            self._records[artefact.tenant_id] = filtered
        self._flush()

    def query(self, tenant_id: str, query: str, limit: int = 5) -> list[RankedArtefact]:
        artefacts = self._records.get(tenant_id, [])
        ranked = [
            RankedArtefact(score=record.similarity(query), artefact=record)
            for record in artefacts
        ]
        ranked.sort(key=lambda item: item.score, reverse=True)
        return ranked[:limit]

    def _tenant_path(self, tenant_id: str) -> Path:
        return self._base_path / f"{tenant_id}.json"

    def _flush(self) -> None:
        for tenant_id, records in self._records.items():
            path = self._tenant_path(tenant_id)
            payload = [record.model_dump() for record in records]
            path.write_text(json.dumps(payload, default=str), encoding="utf-8")

    def _load_from_disk(self) -> None:
        for path in self._base_path.glob("*.json"):
            data = json.loads(path.read_text(encoding="utf-8"))
            tenant_id = path.stem
            self._records[tenant_id] = [ArtefactRecord(**item) for item in data]


class KeywordStore(VectorStore):
    """Alias for vector store; sparse weights live within :class:`ArtefactRecord`."""

    def __init__(self, base_path: Path | str | None = None) -> None:
        super().__init__(base_path or "artifacts/knowledge/keywords")


class ManifestStore:
    def __init__(self, base_path: Path | str | None = None) -> None:
        self._base_path = Path(base_path or "artifacts/knowledge/manifests")
        self._base_path.mkdir(parents=True, exist_ok=True)
        self._manifests: dict[str, TenantManifest] = {}
        self._load_from_disk()

    def write(self, tenant_id: str, artefact_ids: Iterable[str], graph_version: str) -> TenantManifest:
        manifest = TenantManifest(
            tenant_id=tenant_id,
            artefact_ids=list(artefact_ids),
            graph_version=graph_version,
            stored_at=self._now(),
        )
        self._manifests[tenant_id] = manifest
        self._flush(tenant_id)
        return manifest

    def get(self, tenant_id: str) -> TenantManifest | None:
        return self._manifests.get(tenant_id)

    def _manifest_path(self, tenant_id: str) -> Path:
        return self._base_path / f"{tenant_id}.json"

    def _flush(self, tenant_id: str) -> None:
        manifest = self._manifests[tenant_id]
        path = self._manifest_path(tenant_id)
        path.write_text(json.dumps(manifest.model_dump(), default=str), encoding="utf-8")

    def _load_from_disk(self) -> None:
        for path in self._base_path.glob("*.json"):
            data = json.loads(path.read_text(encoding="utf-8"))
            manifest = TenantManifest(**data)
            self._manifests[manifest.tenant_id] = manifest

    @staticmethod
    def _now():  # pragma: no cover - trivial shim
        return datetime.now(timezone.utc)


class GraphStore:
    """Persist graph summaries and edges per tenant."""

    def __init__(self, base_path: Path | str | None = None) -> None:
        self._base_path = Path(base_path or "artifacts/knowledge/graph")
        self._base_path.mkdir(parents=True, exist_ok=True)
        self._graphs: dict[str, Mapping[str, list[dict[str, str | float | list[str]]]]] = {}
        self._load_from_disk()

    def write(
        self,
        tenant_id: str,
        nodes: Iterable[Mapping[str, str]],
        edges: Iterable[Mapping[str, str | float]],
        communities: Iterable[Mapping[str, str | float | list[str]]],
    ) -> None:
        payload = {
            "nodes": [dict(node) for node in nodes],
            "edges": [dict(edge) for edge in edges],
            "communities": [dict(comm) for comm in communities],
        }
        self._graphs[tenant_id] = payload
        self._flush(tenant_id)

    def get(self, tenant_id: str) -> Mapping[str, list[dict[str, str | float | list[str]]]] | None:
        return self._graphs.get(tenant_id)

    def _graph_path(self, tenant_id: str) -> Path:
        return self._base_path / f"{tenant_id}.json"

    def _flush(self, tenant_id: str) -> None:
        payload = self._graphs[tenant_id]
        path = self._graph_path(tenant_id)
        path.write_text(json.dumps(payload, default=str), encoding="utf-8")

    def _load_from_disk(self) -> None:
        for path in self._base_path.glob("*.json"):
            tenant_id = path.stem
            self._graphs[tenant_id] = json.loads(path.read_text(encoding="utf-8"))

