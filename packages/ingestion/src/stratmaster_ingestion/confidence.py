"""Confidence heuristics for parsed document chunks."""

from __future__ import annotations

import math
import re
import string
from statistics import mean
from typing import Iterable


class ConfidenceScorer:
    """Heuristic scorer that approximates OCR/parse quality without ML models."""

    _WORD_RE = re.compile(r"[\w-]{2,}")

    def __init__(self, min_tokens: int = 12) -> None:
        self.min_tokens = min_tokens

    def score(self, text: str) -> float:
        """Return a normalised confidence score between 0 and 1."""

        if not text or not text.strip():
            return 0.0
        cleaned = text.strip()
        total_chars = len(cleaned)
        printable = sum(ch in string.printable for ch in cleaned)
        alpha = sum(ch.isalpha() for ch in cleaned)
        digits = sum(ch.isdigit() for ch in cleaned)
        tokens = self._WORD_RE.findall(cleaned)

        printable_ratio = printable / total_chars
        alpha_ratio = alpha / total_chars
        digit_ratio = digits / total_chars
        whitespace_ratio = sum(ch.isspace() for ch in cleaned) / total_chars
        token_density = len(tokens) / max(total_chars / 5, 1)
        lexical_diversity = (len(set(tokens)) / len(tokens)) if tokens else 0.0
        spacing_quality = 1 - min(abs(whitespace_ratio - 0.18) * 2, 0.6)

        coverage = min(printable_ratio * 0.55 + alpha_ratio * 0.25 + (1 - digit_ratio) * 0.2, 1.0)
        density = min(token_density, 1.0)
        diversity = lexical_diversity

        base_score = 0.5 * coverage + 0.25 * density + 0.15 * diversity + 0.1 * spacing_quality

        if len(tokens) < self.min_tokens:
            penalty = (self.min_tokens - len(tokens)) / self.min_tokens
            base_score *= max(0.25, 1 - penalty)

        entropy = self._character_entropy(cleaned)
        if entropy < 2.5:
            base_score *= 0.75
        elif entropy > 4.5:
            base_score *= 0.9

        return max(0.0, min(round(base_score, 4), 1.0))

    def aggregate(self, scores: Iterable[float]) -> float:
        values = [s for s in scores if 0.0 <= s <= 1.0]
        if not values:
            return 0.0
        return round(mean(values), 4)

    @staticmethod
    def _character_entropy(text: str) -> float:
        counts: dict[str, int] = {}
        for ch in text:
            counts[ch] = counts.get(ch, 0) + 1
        total = len(text)
        entropy = 0.0
        for freq in counts.values():
            p = freq / total
            entropy -= p * math.log(p, 2)
        return entropy