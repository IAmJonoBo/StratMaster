"""Pluggable parsers for different document formats."""

from __future__ import annotations

import csv
import io
import json
import mimetypes
import re
import textwrap
from dataclasses import dataclass
from typing import Iterable, Protocol

from .models import ChunkKind, ChunkMetadata, ChunkStatistics, DocumentPayload


@dataclass(slots=True)
class ParserOutput:
    text: str
    kind: ChunkKind = ChunkKind.TEXT
    source_page: int | None = None


class Parser(Protocol):
    name: str

    def supports(self, payload: DocumentPayload) -> bool:
        ...

    def parse(self, payload: DocumentPayload) -> Iterable[ParserOutput]:
        ...


class PlainTextParser:
    name = "plain-text"
    _CLEAN_RE = re.compile(r"\s+")

    def supports(self, payload: DocumentPayload) -> bool:
        mimetype = payload.mimetype or guess_mimetype(payload.filename)
        return (mimetype or "").startswith("text/")

    def parse(self, payload: DocumentPayload) -> Iterable[ParserOutput]:
        text = payload.content.decode("utf-8", errors="replace")
        normalised = self._CLEAN_RE.sub(" ", text)
        yield ParserOutput(text=normalised.strip(), kind=ChunkKind.TEXT)


class MarkdownParser(PlainTextParser):
    name = "markdown"
    _HTML_RE = re.compile(r"<[^>]+>")

    def supports(self, payload: DocumentPayload) -> bool:
        if payload.filename.lower().endswith((".md", ".markdown")):
            return True
        mimetype = payload.mimetype or guess_mimetype(payload.filename)
        return mimetype in {"text/markdown", "text/x-markdown"}

    def parse(self, payload: DocumentPayload) -> Iterable[ParserOutput]:
        text = payload.content.decode("utf-8", errors="replace")
        without_html = self._HTML_RE.sub(" ", text)
        for line in without_html.splitlines():
            cleaned = line.strip("#> ")
            if cleaned:
                yield ParserOutput(text=cleaned, kind=ChunkKind.TEXT)


class CSVParser:
    name = "csv"

    def supports(self, payload: DocumentPayload) -> bool:
        if payload.filename.lower().endswith((".csv", ".tsv")):
            return True
        mimetype = payload.mimetype or guess_mimetype(payload.filename)
        return mimetype in {"text/csv", "text/tab-separated-values"}

    def parse(self, payload: DocumentPayload) -> Iterable[ParserOutput]:
        text = payload.content.decode("utf-8", errors="replace")
        dialect = csv.excel_tab if "\t" in text.partition("\n")[0] else csv.excel
        reader = csv.reader(io.StringIO(text), dialect=dialect)
        for row in reader:
            if not row:
                continue
            yield ParserOutput(
                text=" | ".join(cell.strip() for cell in row),
                kind=ChunkKind.TABLE,
            )


class JSONParser:
    name = "json"

    def supports(self, payload: DocumentPayload) -> bool:
        if payload.filename.lower().endswith(".json"):
            return True
        mimetype = payload.mimetype or guess_mimetype(payload.filename)
        return mimetype == "application/json"

    def parse(self, payload: DocumentPayload) -> Iterable[ParserOutput]:
        decoded = payload.content.decode("utf-8", errors="replace")
        try:
            data = json.loads(decoded)
        except json.JSONDecodeError:
            yield ParserOutput(text=decoded.strip())
            return
        for chunk in _flatten_json(data):
            yield ParserOutput(text=chunk, kind=ChunkKind.STRUCTURED)


class FallbackBinaryParser:
    name = "binary"

    def supports(self, payload: DocumentPayload) -> bool:
        return True

    def parse(self, payload: DocumentPayload) -> Iterable[ParserOutput]:
        preview = payload.content[:120]
        snippet = preview.decode("utf-8", errors="replace")
        yield ParserOutput(
            text=textwrap.shorten(snippet, width=240, placeholder=" …"),
            kind=ChunkKind.BINARY,
        )


def guess_mimetype(filename: str) -> str | None:
    guessed, _ = mimetypes.guess_type(filename)
    return guessed


def _flatten_json(data: object, prefix: str = "") -> list[str]:
    chunks: list[str] = []
    if isinstance(data, dict):
        for key, value in data.items():
            new_prefix = f"{prefix}{key}: " if prefix else f"{key}: "
            chunks.extend(_flatten_json(value, prefix=new_prefix))
    elif isinstance(data, list):
        for idx, item in enumerate(data, start=1):
            new_prefix = f"{prefix}[{idx}] "
            chunks.extend(_flatten_json(item, prefix=new_prefix))
    else:
        chunks.append(f"{prefix}{data}")
    return chunks


class ParserRegistry:
    """Registry handling parser selection and statistics building."""

    def __init__(self, parsers: Iterable[Parser] | None = None) -> None:
        self.parsers: list[Parser] = list(parsers) if parsers else [
            MarkdownParser(),
            CSVParser(),
            JSONParser(),
            PlainTextParser(),
        ]
        self.fallback = FallbackBinaryParser()

    def select(self, payload: DocumentPayload) -> Parser:
        for parser in self.parsers:
            try:
                if parser.supports(payload):
                    return parser
            except Exception:
                continue
        return self.fallback

    @staticmethod
    def build_metadata(
        *,
        index: int,
        parser: Parser,
        kind: ChunkKind,
        payload: DocumentPayload,
        source_page: int | None = None,
    ) -> ChunkMetadata:
        return ChunkMetadata(
            index=index,
            parser=parser.name,
            kind=kind,
            source_page=source_page,
            source_path=payload.filename,
            mimetype=payload.mimetype or guess_mimetype(payload.filename) or "application/octet-stream",
        )

    @staticmethod
    def build_statistics(text: str) -> ChunkStatistics:
        char_count = len(text)
        word_count = sum(1 for _ in text.split())
        line_count = text.count("\n") + (1 if text else 0)
        whitespace = sum(ch.isspace() for ch in text)
        whitespace_ratio = whitespace / char_count if char_count else 0.0
        return ChunkStatistics(
            char_count=char_count,
            word_count=word_count,
            line_count=line_count,
            whitespace_ratio=round(whitespace_ratio, 4),
        )

