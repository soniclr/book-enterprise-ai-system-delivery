"""Policy-first model routing example.

The example keeps security and capability constraints ahead of price.  It is
deliberately dependency-free and is not a production gateway.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum


class DataClass(IntEnum):
    PUBLIC = 0
    INTERNAL = 1
    SENSITIVE = 2
    HIGHLY_SENSITIVE = 3


@dataclass(frozen=True)
class Channel:
    name: str
    max_data_class: DataClass
    capabilities: frozenset[str]
    cost_rank: int
    latency_rank: int
    available: bool = True


@dataclass(frozen=True)
class RouteRequest:
    task: str
    data_class: DataClass
    required_capability: str
    prefer_low_latency: bool = False


@dataclass(frozen=True)
class RouteDecision:
    channel: str
    reason: str


class NoAllowedRoute(RuntimeError):
    """Raised when policy leaves no approved model path."""


def route(request: RouteRequest, channels: list[Channel]) -> RouteDecision:
    """Choose the cheapest or fastest approved channel.

    Availability, data policy, and required capability are hard constraints.
    They cannot be overridden by cost or latency preferences.
    """

    approved = [
        channel
        for channel in channels
        if channel.available
        and request.data_class <= channel.max_data_class
        and request.required_capability in channel.capabilities
    ]
    if not approved:
        raise NoAllowedRoute(
            f"No channel may process task={request.task!r}, "
            f"data_class={request.data_class.name}, "
            f"capability={request.required_capability!r}"
        )

    if request.prefer_low_latency:
        selected = min(approved, key=lambda item: (item.latency_rank, item.cost_rank))
        preference = "lowest approved latency"
    else:
        selected = min(approved, key=lambda item: (item.cost_rank, item.latency_rank))
        preference = "lowest approved cost"

    return RouteDecision(
        channel=selected.name,
        reason=(
            f"{preference}; channel supports {request.required_capability}; "
            f"policy allows data up to {selected.max_data_class.name}"
        ),
    )
