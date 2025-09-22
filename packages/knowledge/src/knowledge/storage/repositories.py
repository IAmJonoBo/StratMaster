"""In-process repositories backing the knowledge fabric."""

from __future__ import annotations

import json
import logging
from collections import defaultdict
from collections.abc import Iterable, Mapping
from datetime import UTC, datetime
from pathlib import Path

from .contracts import ArtefactRecord, RankedArtefact, TenantManifest

JSON_GLOB_PATTERN = "*.json"


logger = logging.getLogger(__name__)


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
            filtered = [
                rec for rec in records if rec.document_id != artefact.document_id
            ]
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
        # Refresh records from disk to keep in-memory view consistent
        self._load_from_disk()

    def _load_from_disk(self) -> None:
        """Load all tenant records from disk into memory."""
        for tenant_id in self._records.keys():
            # clear to avoid duplication
            self._records[tenant_id] = []
        for path in self._base_path.glob(JSON_GLOB_PATTERN):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            # on-disk partial/corrupt files are skipped intentionally, but we log the issue
            except (OSError, json.JSONDecodeError, UnicodeDecodeError) as exc:
                logger.warning(
                    "VectorStore: skipping unreadable JSON file %s: %s",
                    path,
                    exc,
                )
                continue  # pragma: no cover - ignore partial files
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

    def write(
        self, tenant_id: str, artefact_ids: Iterable[str], graph_version: str
    ) -> TenantManifest:
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
        path.write_text(
            json.dumps(manifest.model_dump(), default=str), encoding="utf-8"
        )
        # Reload manifests to ensure in-memory cache reflects disk
        self._load_from_disk()

    @staticmethod
    def _now() -> datetime:  # pragma: no cover - trivial shim
        return datetime.now(UTC)

    def _load_from_disk(self) -> None:
        """Load manifests from disk into memory."""
        self._manifests.clear()
        for path in self._base_path.glob(JSON_GLOB_PATTERN):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            # skip invalid JSON payloads written by older versions, but log
            except Exception as exc:  # nosec B112
                logger.warning(
                    "ManifestStore: skipping invalid JSON in %s: %s",
                    path,
                    exc,
                )
                continue  # pragma: no cover
            try:
                manifest = TenantManifest(**data)
            # skip invalid JSON payloads written by older versions, but log
            except Exception as exc:  # nosec B112
                logger.warning(
                    "ManifestStore: skipping incompatible manifest in %s: %s",
                    path,
                    exc,
                )
                continue  # pragma: no cover
            self._manifests[manifest.tenant_id] = manifest


class GraphStore:
    """Persist graph summaries and edges per tenant."""

    def __init__(self, base_path: Path | str | None = None) -> None:
        self._base_path = Path(base_path or "artifacts/knowledge/graph")
        self._base_path.mkdir(parents=True, exist_ok=True)
        # Use a permissive value type to accommodate nodes/edges/communities shapes
        self._graphs: dict[str, dict[str, list[dict[str, object]]]] = {}
        self._load_from_disk()

    def write(
        self,
        tenant_id: str,
        nodes: Iterable[Mapping[str, str]],
        edges: Iterable[Mapping[str, str | float]],
        communities: Iterable[Mapping[str, str | float | list[str]]],
    ) -> None:
        payload: dict[str, list[dict[str, object]]] = {
            "nodes": [dict(node) for node in nodes],
            "edges": [dict(edge) for edge in edges],
            "communities": [dict(comm) for comm in communities],
        }
        self._graphs[tenant_id] = payload
        self._flush(tenant_id)

    def get(self, tenant_id: str) -> Mapping[str, list[dict[str, object]]] | None:
        return self._graphs.get(tenant_id)

    def _graph_path(self, tenant_id: str) -> Path:
        return self._base_path / f"{tenant_id}.json"

    def _flush(self, tenant_id: str) -> None:
        payload = self._graphs[tenant_id]
        path = self._graph_path(tenant_id)
        path.write_text(json.dumps(payload, default=str), encoding="utf-8")
        # Reload from disk to ensure cache consistency
        self._load_from_disk()

    def _load_from_disk(self) -> None:
        """Load graph payloads from disk into memory."""
        self._graphs.clear()
        for path in self._base_path.glob(JSON_GLOB_PATTERN):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            # ignore unreadable/partial JSON files, but log
            except Exception as exc:  # nosec B112
                logger.warning(
                    "GraphStore: skipping unreadable JSON file %s: %s",
                    path,
                    exc,
                )
                continue  # pragma: no cover
            tenant_id = path.stem
            # data is expected to be a dict with keys nodes/edges/communities
            if isinstance(data, dict):
                # coerce values to expected list-of-dicts shape when possible
                coerced: dict[str, list[dict[str, object]]] = {}
                for key in ("nodes", "edges", "communities"):
                    raw = data.get(key, [])
                    if isinstance(raw, list):
                        coerced[key] = [
                            dict(item) for item in raw if isinstance(item, dict)
                        ]
                    else:
                        coerced[key] = []
                self._graphs[tenant_id] = coerced
