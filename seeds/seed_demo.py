"""Idempotent loader for StratMaster demo artefacts."""

from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import logging
import os
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from io import BytesIO
from pathlib import Path
from typing import Any

logger = logging.getLogger("stratmaster.seeds")

"""Note: Optional clients are imported inside functions to keep module importable
without those dependencies installed (psycopg, qdrant-client, opensearch-py, minio)."""

DATA_FILE = Path(__file__).with_name("demo-ceps-jtbd-dbas.json")
DEFAULT_BUCKET = "stratmaster-demo"


@dataclass(slots=True)
class SeedConfig:
    dataset_path: Path
    postgres_dsn: str
    qdrant_url: str
    qdrant_collection: str
    opensearch_url: str
    opensearch_index: str
    minio_endpoint: str
    minio_access_key: str
    minio_secret_key: str
    minio_bucket: str
    minio_region: str
    minio_secure: bool

    @staticmethod
    def from_env(dataset_path: Path) -> 'SeedConfig':
        return SeedConfig(
            dataset_path=dataset_path,
            postgres_dsn=os.getenv(
                "SEED_POSTGRES_DSN",
                # No credentials in defaults; use environment variables instead
                "postgresql://localhost:5432/stratmaster",
            ),
            qdrant_url=os.getenv("SEED_QDRANT_URL", "http://localhost:6333"),
            qdrant_collection=os.getenv("SEED_QDRANT_COLLECTION", "stratmaster-demo"),
            opensearch_url=os.getenv("SEED_OPENSEARCH_URL", "http://localhost:9200"),
            opensearch_index=os.getenv("SEED_OPENSEARCH_INDEX", "stratmaster-demo"),
            minio_endpoint=os.getenv("SEED_MINIO_ENDPOINT", "localhost:9000"),
            minio_access_key=os.getenv("SEED_MINIO_ACCESS_KEY", "stratmaster"),
            minio_secret_key=os.getenv("SEED_MINIO_SECRET_KEY", "stratmaster123"),
            minio_bucket=os.getenv("SEED_MINIO_BUCKET", DEFAULT_BUCKET),
            minio_region=os.getenv("SEED_MINIO_REGION", "us-east-1"),
            minio_secure=os.getenv("SEED_MINIO_SECURE", "false").lower()
            in {"1", "true", "yes"},
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Seed demo artefacts across services")
    parser.add_argument(
        "--dataset",
        type=Path,
        default=DATA_FILE,
        help="Path to JSON bundle describing demo artefacts",
    )
    parser.add_argument(
        "--skip",
        nargs="*",
        choices=["postgres", "qdrant", "opensearch", "minio"],
        default=[],
        help="Backends to skip (useful when dependencies are unavailable)",
    )
    return parser.parse_args()


def load_bundle(path: Path) -> Mapping[str, list[dict[str, Any]]]:
    with path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, dict):  # pragma: no cover - guard rail
        raise ValueError("Seed dataset must be a JSON object keyed by asset type")
    return data


def _normalise_timestamp(value: str) -> datetime:
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    dt = datetime.fromisoformat(value)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


def _fingerprint(record: Mapping[str, Any]) -> str:
    canonical = json.dumps(record, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def _vectorize(text: str, size: int = 16) -> list[float]:
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    floats: list[float] = []
    for idx in range(size):
        chunk = digest[idx % len(digest) : (idx % len(digest)) + 2]
        if len(chunk) < 2:
            chunk = chunk.ljust(2, b"\0")
        value = int.from_bytes(chunk, "big") / 65535.0
        floats.append(value)
    return floats


def _prepare_assets(bundle: Mapping[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    prepared: list[dict[str, Any]] = []
    for asset_type, records in bundle.items():
        for record in records:
            base = dict(record)
            source = base.pop("source", {})
            sast = base.pop("sast", source.get("collected_at"))
            if not sast:
                raise ValueError(f"Asset {record.get('id')} missing SAST timestamp")
            timestamp = _normalise_timestamp(sast)
            fingerprint = _fingerprint({"asset_type": asset_type, **record})
            prepared.append(
                {
                    "asset_type": asset_type,
                    "id": record["id"],
                    "title": record.get("title", ""),
                    "summary": record.get("summary", ""),
                    "attributes": {
                        key: value
                        for key, value in base.items()
                        if key not in {"id", "title", "summary"}
                    },
                    "source": {
                        **source,
                        "collected_at": _normalise_timestamp(
                            source.get("collected_at", sast)
                        ).isoformat(),
                    },
                    "sast": timestamp,
                    "fingerprint": fingerprint,
                    "vector": _vectorize(
                        record.get("summary", record.get("title", ""))
                    ),
                }
            )
    return prepared


def seed_postgres(config: SeedConfig, assets: Iterable[Mapping[str, Any]]) -> None:
    try:
        psycopg = importlib.import_module("psycopg")
        types_json = importlib.import_module("psycopg.types.json")
        json_adapter = types_json.Json
    except Exception:  # pragma: no cover - optional client
        logger.warning("psycopg not installed; skipping Postgres seeding")
        return

    logger.info("Seeding Postgres at %s", config.postgres_dsn)
    materialised = list(assets)
    if not materialised:
        logger.info("No assets to persist in Postgres")
        return
    with psycopg.connect(config.postgres_dsn, autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute("CREATE SCHEMA IF NOT EXISTS stratmaster_demo")
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS stratmaster_demo.assets (
                    asset_type TEXT NOT NULL,
                    asset_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    attributes JSONB NOT NULL,
                    provenance JSONB NOT NULL,
                    sast TIMESTAMPTZ NOT NULL,
                    fingerprint TEXT NOT NULL,
                    PRIMARY KEY(asset_type, asset_id)
                )
                """
            )
            for asset in materialised:
                cur.execute(
                    """
                    INSERT INTO stratmaster_demo.assets (
                        asset_type,
                        asset_id,
                        title,
                        summary,
                        attributes,
                        provenance,
                        sast,
                        fingerprint
                    ) VALUES (
                        %(asset_type)s,
                        %(id)s,
                        %(title)s,
                        %(summary)s,
                        %(attributes)s,
                        %(source)s,
                        %(sast)s,
                        %(fingerprint)s
                    )
                    ON CONFLICT (asset_type, asset_id) DO UPDATE SET
                        title = EXCLUDED.title,
                        summary = EXCLUDED.summary,
                        attributes = EXCLUDED.attributes,
                        provenance = EXCLUDED.provenance,
                        sast = EXCLUDED.sast,
                        fingerprint = EXCLUDED.fingerprint
                    """,
                    {
                        **asset,
                        "attributes": json_adapter(asset["attributes"]),
                        "source": json_adapter(asset["source"]),
                    },
                )
    logger.info("Postgres seed complete")


def seed_qdrant(config: SeedConfig, assets: Iterable[Mapping[str, Any]]) -> None:
    try:
        qdrant_mod = importlib.import_module("qdrant_client")
        qdrant_client_cls = qdrant_mod.QdrantClient
    except Exception:  # pragma: no cover - optional client
        logger.warning("qdrant-client not installed; skipping Qdrant seeding")
        return
    logger.info(
        "Seeding Qdrant at %s (collection %s)",
        config.qdrant_url,
        config.qdrant_collection,
    )
    materialised = list(assets)
    if not materialised:
        logger.info("No assets to persist in Qdrant")
        return
    client = qdrant_client_cls(url=config.qdrant_url)
    vectors_config = {"size": len(materialised[0]["vector"]), "distance": "Cosine"}
    client.recreate_collection(
        collection_name=config.qdrant_collection, vectors_config=vectors_config
    )
    points = []
    for asset in materialised:
        points.append(
            (
                f"{asset['asset_type']}::{asset['id']}",
                asset["vector"],
                {
                    "title": asset["title"],
                    "summary": asset["summary"],
                    "asset_type": asset["asset_type"],
                    "fingerprint": asset["fingerprint"],
                    "sast": asset["sast"].isoformat(),
                    "attributes": asset["attributes"],
                    "source": asset["source"],
                },
            )
        )
    client.upsert(collection_name=config.qdrant_collection, points=points)
    logger.info("Qdrant seed complete")


def seed_opensearch(config: SeedConfig, assets: Iterable[Mapping[str, Any]]) -> None:
    try:
        opensearch_mod = importlib.import_module("opensearchpy")
        open_search_cls = opensearch_mod.OpenSearch
    except Exception:  # pragma: no cover - optional client
        logger.warning("opensearch-py not installed; skipping OpenSearch seeding")
        return
    logger.info(
        "Seeding OpenSearch at %s (index %s)",
        config.opensearch_url,
        config.opensearch_index,
    )
    materialised = list(assets)
    if not materialised:
        logger.info("No assets to persist in OpenSearch")
        return
    client = open_search_cls(hosts=[config.opensearch_url])
    if not client.indices.exists(
        index=config.opensearch_index
    ):  # pragma: no branch - defensive
        client.indices.create(
            index=config.opensearch_index,
            body={
                "settings": {"index": {"number_of_shards": 1, "number_of_replicas": 0}},
                "mappings": {
                    "properties": {
                        "title": {"type": "text"},
                        "summary": {"type": "text"},
                        "asset_type": {"type": "keyword"},
                        "fingerprint": {"type": "keyword"},
                        "sast": {"type": "date"},
                    }
                },
            },
        )
    for asset in materialised:
        client.index(
            index=config.opensearch_index,
            id=f"{asset['asset_type']}::{asset['id']}",
            body={
                "title": asset["title"],
                "summary": asset["summary"],
                "asset_type": asset["asset_type"],
                "attributes": asset["attributes"],
                "source": asset["source"],
                "fingerprint": asset["fingerprint"],
                "sast": asset["sast"].isoformat(),
            },
        )
    client.indices.refresh(index=config.opensearch_index)
    logger.info("OpenSearch seed complete")


def seed_minio(config: SeedConfig, assets: Iterable[Mapping[str, Any]]) -> None:
    try:
        minio_mod = importlib.import_module("minio")
        minio_client_cls = minio_mod.Minio
    except Exception:  # pragma: no cover - optional client
        logger.warning("minio client not installed; skipping MinIO seeding")
        return
    logger.info(
        "Seeding MinIO at %s (bucket %s)", config.minio_endpoint, config.minio_bucket
    )
    materialised = list(assets)
    if not materialised:
        logger.info("No assets to persist in MinIO")
        return
    client = minio_client_cls(
        config.minio_endpoint,
        access_key=config.minio_access_key,
        secret_key=config.minio_secret_key,
        secure=config.minio_secure,
        region=config.minio_region,
    )
    if not client.bucket_exists(config.minio_bucket):  # pragma: no branch - defensive
        client.make_bucket(config.minio_bucket, location=config.minio_region)
    manifest = {
        "generated_at": datetime.now(UTC).isoformat(),
        "assets": [
            {
                "asset_type": asset["asset_type"],
                "id": asset["id"],
                "fingerprint": asset["fingerprint"],
                "sast": asset["sast"].isoformat(),
            }
            for asset in materialised
        ],
    }
    manifest_bytes = json.dumps(manifest, sort_keys=True, indent=2).encode("utf-8")
    client.put_object(
        config.minio_bucket,
        "manifests/demo-assets.json",
        BytesIO(manifest_bytes),
        length=len(manifest_bytes),
        content_type="application/json",
    )
    for asset in materialised:
        key = f"assets/{asset['asset_type']}/{asset['id']}.json"
        payload = json.dumps(
            {
                "title": asset["title"],
                "summary": asset["summary"],
                "attributes": asset["attributes"],
                "source": asset["source"],
                "fingerprint": asset["fingerprint"],
                "sast": asset["sast"].isoformat(),
            },
            indent=2,
            sort_keys=True,
        ).encode("utf-8")
        client.put_object(
            config.minio_bucket,
            key,
            BytesIO(payload),
            length=len(payload),
            content_type="application/json",
        )
    logger.info("MinIO seed complete")


def main() -> None:
    args = parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    config = SeedConfig.from_env(args.dataset)
    bundle = load_bundle(args.dataset)
    assets = _prepare_assets(bundle)

    logger.info("Loaded %d assets from %s", len(assets), args.dataset)

    if "postgres" not in args.skip:
        seed_postgres(config, assets)
    if "qdrant" not in args.skip:
        seed_qdrant(config, assets)
    if "opensearch" not in args.skip:
        seed_opensearch(config, assets)
    if "minio" not in args.skip:
        seed_minio(config, assets)

    logger.info("Seeding complete")


if __name__ == "__main__":
    main()
