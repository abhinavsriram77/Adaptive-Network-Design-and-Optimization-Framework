"""Base contracts and data models for all-pairs routing algorithms."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class NegativeCycleError(Exception):
    """Raised when a graph contains a reachable negative weight cycle."""
    pass


@dataclass
class PathInfo:
    """Detailed summary of a reconstructed shortest path between two nodes.
    
    Attributes:
        source: Starting node identifier.
        target: Destination node identifier.
        distance: Sum of primary metric costs along the path.
        path: Ordered list of node IDs traversed from source to target.
        hop_count: Number of communication hops (len(path) - 1).
        total_latency_ms: Sum of transmission and propagation latencies.
        bottleneck_bandwidth_gbps: Minimum link bandwidth along the route.
        exists: True if a reachable path connects source to target.
    """
    source: str
    target: str
    distance: float
    path: List[str] = field(default_factory=list)
    hop_count: int = 0
    total_latency_ms: float = 0.0
    bottleneck_bandwidth_gbps: float = 0.0
    exists: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source": self.source,
            "target": self.target,
            "distance": self.distance,
            "path": list(self.path),
            "hop_count": self.hop_count,
            "total_latency_ms": self.total_latency_ms,
            "bottleneck_bandwidth_gbps": self.bottleneck_bandwidth_gbps,
            "exists": self.exists,
        }


@dataclass
class RoutingResult:
    """Full-mesh all-pairs routing matrix output with path reconstruction capabilities.
    
    Attributes:
        node_ids: Sorted list of node identifiers matching matrix indices.
        distance_matrix: 2D float matrix where D[i][j] is the shortest path distance.
        next_hop_matrix: 2D index matrix where Next[i][j] is the next hop vertex index.
        execution_time_ms: Runtime in milliseconds.
        relaxations_count: Count of successful edge relaxation operations.
        comparisons_count: Total triple-loop comparison operations executed (Theta(|V|^3)).
        metric_used: Primary optimization metric ("latency_ms", "weight", etc.).
        has_negative_cycle: Whether a negative cycle was discovered.
        metadata: Diagnostic and performance metadata.
    """
    node_ids: List[str]
    distance_matrix: List[List[float]]
    next_hop_matrix: List[List[Optional[int]]]
    execution_time_ms: float = 0.0
    relaxations_count: int = 0
    comparisons_count: int = 0
    metric_used: str = "latency_ms"
    has_negative_cycle: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self._id_to_idx = {nid: i for i, nid in enumerate(self.node_ids)}

    def get_distance(self, source: str, target: str) -> float:
        """Query shortest path distance between source and target."""
        if source not in self._id_to_idx or target not in self._id_to_idx:
            raise KeyError(f"Invalid endpoints: {source!r} -> {target!r}")
        i = self._id_to_idx[source]
        j = self._id_to_idx[target]
        return self.distance_matrix[i][j]

    def reconstruct_path_indices(self, u_idx: int, v_idx: int) -> List[int]:
        """Reconstruct vertex index sequence using next-hop pointers."""
        if self.distance_matrix[u_idx][v_idx] == math.inf:
            return []
        if self.next_hop_matrix[u_idx][v_idx] is None:
            return []

        path = [u_idx]
        curr = u_idx
        visited_indices = {curr}

        while curr != v_idx:
            next_step = self.next_hop_matrix[curr][v_idx]
            if next_step is None:
                return []
            if next_step in visited_indices:
                # Cycle guard for corrupted or negative cycles
                break
            visited_indices.add(next_step)
            path.append(next_step)
            curr = next_step

        return path

    def network_diameter(self) -> float:
        """Maximum finite shortest-path distance between any connected pair of vertices."""
        max_dist = 0.0
        n = len(self.node_ids)
        for i in range(n):
            for j in range(n):
                if i != j and self.distance_matrix[i][j] != math.inf:
                    if self.distance_matrix[i][j] > max_dist:
                        max_dist = self.distance_matrix[i][j]
        return max_dist

    def reachability_ratio(self) -> float:
        """Fraction of directed node pairs (u, v) that are connected by a finite path."""
        n = len(self.node_ids)
        if n <= 1:
            return 1.0
        total_pairs = n * (n - 1)
        reachable = 0
        for i in range(n):
            for j in range(n):
                if i != j and self.distance_matrix[i][j] != math.inf:
                    reachable += 1
        return reachable / total_pairs

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_count": len(self.node_ids),
            "execution_time_ms": self.execution_time_ms,
            "relaxations_count": self.relaxations_count,
            "comparisons_count": self.comparisons_count,
            "metric_used": self.metric_used,
            "network_diameter": self.network_diameter(),
            "reachability_ratio": self.reachability_ratio(),
            "has_negative_cycle": self.has_negative_cycle,
            "metadata": dict(self.metadata),
        }
