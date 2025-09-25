"""Experimentation helpers for CUPED and sequential testing."""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable, Sequence


def cuped_adjustment(outcomes: Sequence[float], covariate: Sequence[float]) -> list[float]:
    if len(outcomes) != len(covariate):
        raise ValueError("Outcomes and covariate must be the same length")
    n = len(outcomes)
    if n == 0:
        return []
    mean_outcome = sum(outcomes) / n
    mean_covariate = sum(covariate) / n
    covariance = sum((x - mean_outcome) * (c - mean_covariate) for x, c in zip(outcomes, covariate))
    variance = sum((c - mean_covariate) ** 2 for c in covariate)
    if variance == 0:
        theta = 0.0
    else:
        theta = covariance / variance
    adjusted = [x - theta * (c - mean_covariate) for x, c in zip(outcomes, covariate)]
    return adjusted


@dataclass(slots=True)
class SPRTState:
    alpha: float
    beta: float
    p0: float
    p1: float
    lower_boundary: float
    upper_boundary: float
    log_likelihood: float = 0.0

    @classmethod
    def create(cls, alpha: float, beta: float, p0: float, p1: float) -> "SPRTState":
        lower = math.log(beta / (1 - alpha))
        upper = math.log((1 - beta) / alpha)
        return cls(alpha=alpha, beta=beta, p0=p0, p1=p1, lower_boundary=lower, upper_boundary=upper)

    def update(self, success: bool) -> str:
        likelihood_ratio = math.log(self.p1 / self.p0) if success else math.log((1 - self.p1) / (1 - self.p0))
        self.log_likelihood += likelihood_ratio
        if self.log_likelihood >= self.upper_boundary:
            return "accept_alt"
        if self.log_likelihood <= self.lower_boundary:
            return "accept_null"
        return "continue"


def sequential_sprt(alpha: float, beta: float, p0: float, p1: float, samples: Iterable[bool]) -> str:
    state = SPRTState.create(alpha=alpha, beta=beta, p0=p0, p1=p1)
    verdict = "continue"
    for observation in samples:
        verdict = state.update(bool(observation))
        if verdict != "continue":
            break
    return verdict
