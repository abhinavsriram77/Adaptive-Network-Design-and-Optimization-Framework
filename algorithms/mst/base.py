"""Abstract base definitions and result contracts for MST algorithms."""

from __future__ import annotations

import math
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Set

from core.edge import NetworkEdge
from core.graph import NetworkGraph


class GraphDisconnectedError(Exception):
    """Raised when an MST algorithm encounters a disconnected graph."""
    pass


@dataclass
class MSTResult:
    """Encapsulates the output and performance telemetry of an MST computation.
    
    Attributes:
        edges: List of NetworkEdge links included in the minimum spanning tree/forest.
        total_weight: Sum of edge weights in the solution.
        execution_time_ms: Wall-clock execution time in milliseconds.
        operations_count: Count of critical algorithmic operations (e.g. comparisons, DSU/heap ops).
        algorithm_name: Identifier of the solver that generated the result.
        is_spanning_tree: True if the result spans all vertices in a single connected tree.
        components_count: Number of disconnected tree components (1 for MST, >1 for MSF).
        metadata: Additional diagnostic and profile metrics.
    """
    edges: List[NetworkEdge]
    total_weight: float
    execution_time_ms: float = 0.0
    operations_count: int = 0
    algorithm_name: str = "Unknown"
    is_spanning_tree: bool = True
    components_count: int = 1
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if math.isnan(self.total_weight) or math.isinf(self.total_weight) or self.total_weight < 0:
            raise ValueError(f"Total weight must be a non-negative finite number, got: {self.total_weight}")

    @property
    def total_latency_ms(self) -> float:
        """Sum of transmission latencies across the spanning backbone."""
        return sum(e.latency_ms for e in self.edges)

    @property
    def min_bandwidth_gbps(self) -> float:
        """Bottleneck capacity along the spanning tree."""
        if not self.edges:
            return 0.0
        return min(e.bandwidth_gbps for e in self.edges)

    @property
    def average_reliability(self) -> float:
        """Mean reliability score across spanning tree links."""
        if not self.edges:
            return 0.0
        return sum(e.reliability_score for e in self.edges) / len(self.edges)

    def spanned_nodes(self) -> Set[str]:
        """Set of node IDs covered by the spanning edges."""
        nodes: Set[str] = set()
        for edge in self.edges:
            nodes.add(edge.u)
            nodes.add(edge.v)
        return nodes

    def to_dict(self) -> Dict[str, Any]:
        """Serialize result to dictionary format."""
        return {
            "algorithm_name": self.algorithm_name,
            "total_weight": self.total_weight,
            "edge_count": len(self.edges),
            "execution_time_ms": self.execution_time_ms,
            "operations_count": self.operations_count,
            "is_spanning_tree": self.is_spanning_tree,
            "components_count": self.components_count,
            "total_latency_ms": self.total_latency_ms,
            "min_bandwidth_gbps": self.min_bandwidth_gbps,
            "average_reliability": self.average_reliability,
            "edges": [e.to_dict() for e in self.edges],
            "metadata": dict(self.metadata),
        }


class BaseMSTSolver(ABC):
    """Abstract base class for Minimum Spanning Tree algorithms."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable algorithm designation."""
        pass

    @abstractmethod
    def solve(self, graph: NetworkGraph, allow_forest: bool = False) -> MSTResult:
        """Compute the Minimum Spanning Tree (or Forest) for the given graph.
        
        Args:
            graph: The NetworkGraph to optimize.
            allow_forest: If False and the graph is disconnected, raises GraphDisconnectedError.
                          If True, computes Minimum Spanning Forest across all components.
                          
        Returns:
            MSTResult with selected edges and operational metrics.
            
        Raises:
            GraphDisconnectedError: If allow_forest is False and graph is disconnected.
        """
        pass
