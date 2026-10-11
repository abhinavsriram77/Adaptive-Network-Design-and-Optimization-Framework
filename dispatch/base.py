"""Abstract base contracts and result representations for TSP field dispatch."""

from __future__ import annotations

import math
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List

from dispatch.site import DispatchSite


@dataclass
class TourManifest:
    """Optimal closed field maintenance tour visiting all required incident sites.
    
    Attributes:
        site_sequence: Ordered list of DispatchSite locations in the closed tour (depot -> sites -> depot).
        total_distance: Total road or transmission cost traversed along the tour.
        total_service_time_mins: Sum of on-site service durations at visited sites.
        total_mission_time_mins: Combined transit time + service duration.
        is_exact_optimal: True if provably optimal via Branch-and-Bound.
        optimality_gap_pct: Bounded gap percentage if solved via heuristic approximation.
        solver_name: Identifier of the algorithm used.
        execution_time_ms: Solver runtime in milliseconds.
        nodes_explored: Branch-and-Bound state space nodes generated.
        nodes_pruned: Branch-and-Bound search branches pruned.
        metadata: Diagnostic and performance telemetry.
    """
    site_sequence: List[DispatchSite]
    total_distance: float
    total_service_time_mins: float = 0.0
    total_mission_time_mins: float = 0.0
    is_exact_optimal: bool = True
    optimality_gap_pct: float = 0.0
    solver_name: str = ""
    execution_time_ms: float = 0.0
    nodes_explored: int = 0
    nodes_pruned: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def tour_node_ids(self) -> List[str]:
        """Ordered sequence of site IDs in the tour."""
        return [site.id for site in self.site_sequence]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "solver_name": self.solver_name,
            "total_distance": round(self.total_distance, 3),
            "total_service_time_mins": round(self.total_service_time_mins, 1),
            "total_mission_time_mins": round(self.total_mission_time_mins, 1),
            "is_exact_optimal": self.is_exact_optimal,
            "optimality_gap_pct": round(self.optimality_gap_pct, 2),
            "stops_count": len(self.site_sequence),
            "tour_sequence": self.tour_node_ids(),
            "execution_time_ms": round(self.execution_time_ms, 3),
            "nodes_explored": self.nodes_explored,
            "nodes_pruned": self.nodes_pruned,
            "metadata": dict(self.metadata),
        }


class BaseTSPSolver(ABC):
    """Abstract interface for Traveling Salesperson Problem solvers."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Descriptive solver designation."""
        pass

    @abstractmethod
    def solve(
        self,
        sites: List[DispatchSite],
        distance_matrix: List[List[float]],
    ) -> TourManifest:
        """Compute the optimal (or bounded) TSP tour given sites and cost matrix.
        
        Args:
            sites: List of DispatchSite instances where sites[0] is the starting depot.
            distance_matrix: n x n float cost matrix where matrix[i][j] is travel cost.
            
        Returns:
            TourManifest detailing turn-by-turn maintenance sequence and metrics.
        """
        pass

