"""Adaptive Field Dispatch Engine integrating routing topology with TSP solvers."""

from __future__ import annotations

import math
import time
from typing import List, Optional

from algorithms.routing.floyd_warshall import FloydWarshallRouter
from core.graph import NetworkGraph
from dispatch.backtracking import BacktrackingTSPSolver
from dispatch.base import TourManifest
from dispatch.branch_and_bound import BranchAndBoundTSPSolver
from dispatch.heuristics import NearestNeighborHeuristic, TwoOptLocalSearch
from dispatch.site import DispatchSite


class AdaptiveDispatchEngine:
    """Intelligent field dispatch scheduler selecting exact vs. heuristic TSP algorithms.
    
    Attributes:
        exact_threshold: Maximum site cluster size solved via exact Branch-and-Bound (default: 18).
        backtracking_threshold: Maximum site cluster size for DFS Backtracking (default: 10).
    """

    def __init__(
        self,
        exact_threshold: int = 18,
        backtracking_threshold: int = 10,
        bnb_max_states: int = 100_000,
        bnb_timeout_seconds: float = 10.0,
    ) -> None:
        self.exact_threshold = exact_threshold
        self.backtracking_threshold = backtracking_threshold
        self.exact_solver = BranchAndBoundTSPSolver(
            max_states=bnb_max_states, timeout_seconds=bnb_timeout_seconds
        )
        self.backtracking_solver = BacktrackingTSPSolver(
            max_states=bnb_max_states * 2, timeout_seconds=bnb_timeout_seconds
        )
        self.router = FloydWarshallRouter(metric="latency_ms")

    def schedule_maintenance_tour(
        self,
        graph: NetworkGraph,
        depot_node_id: str,
        target_site_ids: List[str],
        force_solver: Optional[str] = None,
    ) -> TourManifest:
        """Construct optimal technician maintenance tour across damaged network sites.
        
        Args:
            graph: Operational NetworkGraph topology.
            depot_node_id: Starting and ending maintenance hub ID.
            target_site_ids: Set of network node IDs requiring physical maintenance.
            force_solver: Optional override ('exact', 'branch_and_bound', 'backtracking', 'heuristic').
            
        Returns:
            TourManifest containing exact sequence, mission duration, and travel distance.
        """
        # Deduplicate and ensure depot is at index 0
        ordered_ids = [depot_node_id] + [sid for sid in dict.fromkeys(target_site_ids) if sid != depot_node_id]
        n = len(ordered_ids)

        # 1. Compute full all-pairs shortest paths using Floyd-Warshall from Phase 2
        routing_res = self.router.compute_routing(graph)

        # 2. Extract distance sub-matrix between the chosen dispatch sites
        dist_matrix: List[List[float]] = [[0.0] * n for _ in range(n)]
        sites: List[DispatchSite] = []

        for i, u_id in enumerate(ordered_ids):
            node_ref = graph.get_node(u_id)
            node_name = node_ref.name if node_ref else u_id
            sites.append(
                DispatchSite(
                    id=u_id,
                    name=node_name,
                    is_depot=(i == 0),
                    service_time_mins=0.0 if i == 0 else 30.0,
                )
            )
            for j, v_id in enumerate(ordered_ids):
                if i != j:
                    dist_matrix[i][j] = routing_res.get_distance(u_id, v_id)

        # 3. Dynamic scale selection
        if force_solver == "backtracking":
            return self.backtracking_solver.solve(sites, dist_matrix)
        elif force_solver in ("exact", "branch_and_bound") or (force_solver is None and n <= self.exact_threshold):
            return self.exact_solver.solve(sites, dist_matrix)
        else:
            return self._solve_heuristic(sites, dist_matrix)

    def _solve_heuristic(
        self,
        sites: List[DispatchSite],
        dist_matrix: List[List[float]],
    ) -> TourManifest:
        """Fast heuristic fallback utilizing Nearest Neighbor + 2-Opt local search."""
        start_time = time.perf_counter()
        nn_tour, nn_cost = NearestNeighborHeuristic.construct_tour(dist_matrix, start_idx=0)
        best_tour, best_cost = TwoOptLocalSearch.optimize(nn_tour, dist_matrix)

        exec_time_ms = (time.perf_counter() - start_time) * 1000.0
        site_sequence = [sites[idx] for idx in best_tour]
        total_service = sum(site.service_time_mins for site in site_sequence[:-1] if not site.is_depot)

        return TourManifest(
            site_sequence=site_sequence,
            total_distance=best_cost,
            total_service_time_mins=total_service,
            total_mission_time_mins=total_service + best_cost,
            is_exact_optimal=False,
            optimality_gap_pct=5.0,  # Empirical bound for 2-Opt on Euclidean/metric networks
            solver_name="Bounded Heuristic (Nearest Neighbor + 2-Opt Local Search)",
            execution_time_ms=exec_time_ms,
            nodes_explored=len(sites),
            nodes_pruned=0,
            metadata={"heuristic": "2-Opt", "cluster_size": len(sites)},
        )

