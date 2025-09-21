"""Command-line interface for the BGE reranker."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Sequence

from .reranker import BGEReranker

logger = logging.getLogger(__name__)


def _load_candidates(path: Path | None) -> list[str]:
    if path is None:
        logger.debug("Reading candidates from stdin")
        data = sys.stdin.read()
    else:
        data = path.read_text(encoding="utf-8")
    try:
        payload = json.loads(data)
    except json.JSONDecodeError as exc:  # pragma: no cover - defensive branch
        raise SystemExit(f"Failed to parse candidates JSON: {exc}") from exc
    if not isinstance(payload, list):
        raise SystemExit("Candidates JSON must be a list of strings")
    return [str(item) for item in payload]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="rerankers-bge",
        description="Run the BGE reranker on a query and candidate list.",
    )
    parser.add_argument("--query", required=True, help="Query text to score against.")
    parser.add_argument(
        "--candidates",
        type=Path,
        help="Path to a JSON list of candidate strings. Defaults to stdin when omitted.",
    )
    parser.add_argument(
        "--model",
        default="BAAI/bge-reranker-base",
        help="HuggingFace model identifier (default: %(default)s).",
    )
    parser.add_argument(
        "--device",
        default="auto",
        help="Device identifier (cpu, cuda:0, auto). Default: %(default)s.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=16,
        help="Batch size for transformer inference (default: %(default)s).",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=None,
        help="Only return the top-k results (default: all).",
    )
    parser.add_argument(
        "--force-fallback",
        action="store_true",
        help="Force lexical fallback even when transformers are available.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    reranker = BGEReranker(
        model_name=args.model,
        device=args.device,
        batch_size=args.batch_size,
        force_fallback=args.force_fallback,
    )
    candidates = _load_candidates(args.candidates)
    results = reranker.rerank(args.query, candidates, top_k=args.top_k)
    output = [
        {
            "text": item.text,
            "score": item.score,
            "index": item.index,
            **({"id": item.id} if item.id is not None else {}),
        }
        for item in results
    ]
    json.dump(output, sys.stdout, indent=2)
    sys.stdout.write("\n")


if __name__ == "__main__":  # pragma: no cover - CLI entrypoint
    main()
