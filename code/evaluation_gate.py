"""Evaluation and release-gate example."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from math import ceil
from statistics import mean


class ReleaseStatus(str, Enum):
    PASS = "pass"
    CONDITIONAL = "conditional"
    BLOCKED = "blocked"


@dataclass(frozen=True)
class EvalResult:
    sample_id: str
    quality: float
    latency_ms: int
    cost: float
    blocker: str | None = None


@dataclass(frozen=True)
class GateConfig:
    min_average_quality: float
    max_p95_latency_ms: int
    max_average_cost: float


@dataclass(frozen=True)
class GateDecision:
    status: ReleaseStatus
    reasons: tuple[str, ...]


def _percentile_95(values: list[int]) -> int:
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, ceil(len(ordered) * 0.95) - 1))
    return ordered[index]


def evaluate(results: list[EvalResult], config: GateConfig) -> GateDecision:
    if not results:
        return GateDecision(ReleaseStatus.BLOCKED, ("no evaluation results",))

    blockers = tuple(
        f"{result.sample_id}: {result.blocker}"
        for result in results
        if result.blocker
    )
    if blockers:
        return GateDecision(ReleaseStatus.BLOCKED, blockers)

    reasons: list[str] = []
    if mean(result.quality for result in results) < config.min_average_quality:
        reasons.append("average quality below threshold")
    if _percentile_95([result.latency_ms for result in results]) > config.max_p95_latency_ms:
        reasons.append("P95 latency above threshold")
    if mean(result.cost for result in results) > config.max_average_cost:
        reasons.append("average cost above threshold")

    if reasons:
        return GateDecision(ReleaseStatus.CONDITIONAL, tuple(reasons))
    return GateDecision(ReleaseStatus.PASS, ("all configured gates passed",))
