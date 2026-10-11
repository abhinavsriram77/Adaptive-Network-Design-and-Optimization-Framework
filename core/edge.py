"""Edge domain model for communication links and transit channels.

Encapsulates multi-attribute transmission metrics including latency,
bandwidth capacity, reliability, and edge weight for optimization solvers.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Dict, Tuple


@dataclass
class NetworkEdge:
    """Interconnecting communication link between two network nodes.
    
    Attributes:
        u: Identifier of the source or first endpoint node.
        v: Identifier of the destination or second endpoint node.
        weight: Primary optimization cost metric (used by MST and shortest-path solvers).
        latency_ms: Link propagation and transmission delay in milliseconds.
        bandwidth_gbps: Channel capacity in Gigabits per second.
        reliability_score: Operational availability metric in [0.0, 1.0].
        directed: Whether the link is directional or bidirectional (undirected).
        metadata: Domain-specific parameters (e.g., physical fiber medium, cable length).
    """
    u: str
    v: str
    weight: float
    latency_ms: float = 1.0
    bandwidth_gbps: float = 10.0
    reliability_score: float = 0.99
    directed: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.u or not isinstance(self.u, str):
            raise ValueError(f"Endpoint 'u' must be a non-empty string, got: {self.u!r}")
        if not self.v or not isinstance(self.v, str):
            raise ValueError(f"Endpoint 'v' must be a non-empty string, got: {self.v!r}")
        if self.u == self.v:
            raise ValueError(f"Self-loop edges are not allowed in backbone topologies (node: {self.u!r})")
        if math.isnan(self.weight) or math.isinf(self.weight) or self.weight < 0.0:
            raise ValueError(f"Edge weight must be a non-negative finite number, got: {self.weight}")
        if self.latency_ms < 0.0:
            raise ValueError(f"Latency must be non-negative, got: {self.latency_ms}")
        if self.bandwidth_gbps <= 0.0:
            raise ValueError(f"Bandwidth must be strictly positive, got: {self.bandwidth_gbps}")
        if not (0.0 <= self.reliability_score <= 1.0):
            raise ValueError(f"Reliability score must be within [0.0, 1.0], got: {self.reliability_score}")

    @property
    def endpoints(self) -> Tuple[str, str]:
        """Return the directed pair (u, v)."""
        return self.u, self.v

    @property
    def canonical_endpoints(self) -> Tuple[str, str]:
        """Return order-independent pair for undirected edges, or (u, v) for directed edges."""
        if self.directed:
            return self.u, self.v
        return (self.u, self.v) if self.u <= self.v else (self.v, self.u)

    def reverse(self) -> NetworkEdge:
        """Create a reverse copy of the current edge."""
        return NetworkEdge(
            u=self.v,
            v=self.u,
            weight=self.weight,
            latency_ms=self.latency_ms,
            bandwidth_gbps=self.bandwidth_gbps,
            reliability_score=self.reliability_score,
            directed=self.directed,
            metadata=dict(self.metadata),
        )

    def __hash__(self) -> int:
        return hash((self.canonical_endpoints, self.directed))

    def __eq__(self, other: object) -> bool:
        if isinstance(other, NetworkEdge):
            return self.directed == other.directed and self.canonical_endpoints == other.canonical_endpoints
        return False

    def __lt__(self, other: NetworkEdge) -> bool:
        if not isinstance(other, NetworkEdge):
            return NotImplemented
        return (self.weight, self.latency_ms, self.canonical_endpoints) < (
            other.weight,
            other.latency_ms,
            other.canonical_endpoints,
        )

    def __le__(self, other: NetworkEdge) -> bool:
        if not isinstance(other, NetworkEdge):
            return NotImplemented
        return self == other or self < other

    def __gt__(self, other: NetworkEdge) -> bool:
        if not isinstance(other, NetworkEdge):
            return NotImplemented
        return not (self <= other)

    def __ge__(self, other: NetworkEdge) -> bool:
        if not isinstance(other, NetworkEdge):
            return NotImplemented
        return not (self < other)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize edge attributes to a dictionary."""
        return {
            "u": self.u,
            "v": self.v,
            "weight": self.weight,
            "latency_ms": self.latency_ms,
            "bandwidth_gbps": self.bandwidth_gbps,
            "reliability_score": self.reliability_score,
            "directed": self.directed,
            "metadata": dict(self.metadata),
        }
