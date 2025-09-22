"""GraphRAG materialisation utilities."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Iterable

from ..storage.contracts import ArtefactRecord, CommunitySummary, GraphEdge, GraphNode


@dataclass(slots=True)
class GraphArtefacts:
    nodes: list[GraphNode]
    edges: list[GraphEdge]
    summaries: list[CommunitySummary]


class GraphMaterialiser:
    """Create lightweight communities grouped by shared tags or keyphrases."""

    def __init__(self, max_nodes_per_community: int = 5) -> None:
        self._max_nodes = max_nodes_per_community

    def build(self, artefacts: Iterable[ArtefactRecord]) -> GraphArtefacts:
        buckets: dict[str, list[ArtefactRecord]] = defaultdict(list)
        for artefact in artefacts:
            tags = artefact.tags or list(artefact.sparse_terms.keys())[:3]
            if not tags:
                buckets["general"].append(artefact)
                continue
            for tag in tags:
                buckets[tag.lower()].append(artefact)
        nodes: list[GraphNode] = []
        edges: list[GraphEdge] = []
        summaries: list[CommunitySummary] = []
        for idx, (tag, records) in enumerate(sorted(buckets.items())):
            community_id = f"comm-{idx+1}"
            nodes.append(
                GraphNode(id=community_id, label=tag.title(), type="community")
            )
            key_entities: list[str] = []
            for artefact in records[: self._max_nodes]:
                node_id = f"node-{community_id}-{artefact.document_id}"
                label = artefact.title
                nodes.append(GraphNode(id=node_id, label=label, type="artefact"))
                edges.append(
                    GraphEdge(
                        source=community_id,
                        target=node_id,
                        relation="references",
                        weight=round(1.0 / (records.index(artefact) + 1), 2),
                    )
                )
                key_entities.extend(artefact.tags)
            snippet_counter = Counter(key_entities)
            top_entities = [item[0] for item in snippet_counter.most_common(3)]
            summary_text = "; ".join(
                artefact.summary for artefact in records[: self._max_nodes]
            )[:280]
            summaries.append(
                CommunitySummary(
                    community_id=community_id,
                    title=tag.title(),
                    summary=summary_text or f"Community centred on {tag}",
                    representative_nodes=top_entities or [tag],
                    score=min(1.0, 0.6 + len(records) * 0.05),
                )
            )
        return GraphArtefacts(nodes=nodes, edges=edges, summaries=summaries)
