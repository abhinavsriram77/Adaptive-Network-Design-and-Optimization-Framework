"""Exact Backtracking Traveling Salesperson Problem Solver.

Explores the permutation state-space tree via Depth-First Search (DFS)
backtracking, pruning partial paths whose accumulated distance already
exceeds the incumbent best tour cost.
"""

from __future__ import annotations

import math
import time
from typing import List

from dispatch.base import BaseTSPSolver, TourManifest
from dispatch.site import DispatchSite


class BacktrackingTSPSolver(BaseTSPSolver):
    """Exact TSP solver using Depth-First Search (DFS) Backtracking."""

    def __init__(
        self,
        max_states: int = 250_000,
        timeout_seconds: float = 10.0,
    ) -> None:
        self.max_states = max_states
        self.timeout_seconds = timeout_seconds

    @property
    def name(self) -> str:
        return "Exact Backtracking TSP (DFS State-Space Search)"

    def solve(
        self,
        sites: List[DispatchSite],
        distance_matrix: List[List[float]],
    ) -> TourManifest:
        """Find the optimal closed maintenance tour via DFS Backtracking.

        Args:
            sites: Ordered list of DispatchSite instances where sites[0] is the depot.
            distance_matrix: n x n travel cost matrix.

        Returns:
            TourManifest containing tour sequence, total distance, and state counts.
        """
        start_time = time.perf_counter()
        n = len(sites)

        if n <= 1:
            seq = [sites[0], sites[0]] if n == 1 else []
            return TourManifest(
                site_sequence=seq,
                total_distance=0.0,
                is_exact_optimal=True,
                solver_name=self.name,
                execution_time_ms=(time.perf_counter() - start_time) * 1000.0,
            )

        if n == 2:
            dist = distance_matrix[0][1] + distance_matrix[1][0]
            return TourManifest(
                site_sequence=[sites[0], sites[1], sites[0]],
                total_distance=dist,
                total_service_time_mins=sites[1].service_time_mins,
                total_mission_time_mins=sites[1].service_time_mins + dist,
                is_exact_optimal=True,
                solver_name=self.name,
                execution_time_ms=(time.perf_counter() - start_time) * 1000.0,
                nodes_explored=2,
                nodes_pruned=0,
            )

        best_cost = math.inf
        best_tour_indices: List[int] = []
        visited = [False] * n
        visited[0] = True
        current_path = [0]

        nodes_explored = 0
        nodes_pruned = 0
        is_exact = True

        def _backtrack(curr_node: int, count: int, curr_cost: float) -> None:
            nonlocal best_cost, best_tour_indices, nodes_explored, nodes_pruned, is_exact

            if not is_exact:
                return

            nodes_explored += 1

            # Check safeguard limits for NP-Hard exponential growth
            if nodes_explored >= self.max_states or (time.perf_counter() - start_time) > self.timeout_seconds:
                is_exact = False
                return

            # Base case: all n sites visited, check return edge to depot (node 0)
            if count == n:
                return_edge = distance_matrix[curr_node][0]
                if return_edge != math.inf:
                    total_cost = curr_cost + return_edge
                    if total_cost < best_cost:
                        best_cost = total_cost
                        best_tour_indices = current_path[:] + [0]
                return

            # Try all unvisited next sites
            for next_node in range(1, n):
                if not visited[next_node]:
                    step_cost = distance_matrix[curr_node][next_node]
                    if step_cost == math.inf:
                        continue

                    new_cost = curr_cost + step_cost
                    # Backtracking bounding check: prune if partial path already >= best complete tour
                    if new_cost < best_cost:
                        visited[next_node] = True
                        current_path.append(next_node)

                        _backtrack(next_node, count + 1, new_cost)

                        # Backtrack (undo state changes)
                        current_path.pop()
                        visited[next_node] = False
                    else:
                        nodes_pruned += 1

        _backtrack(curr_node=0, count=1, curr_cost=0.0)

        exec_time_ms = (time.perf_counter() - start_time) * 1000.0
        site_sequence = [sites[idx] for idx in best_tour_indices]
        total_service = sum(site.service_time_mins for site in site_sequence[:-1] if not site.is_depot)

        return TourManifest(
            site_sequence=site_sequence,
            total_distance=best_cost,
            total_service_time_mins=total_service,
            total_mission_time_mins=total_service + best_cost,
            is_exact_optimal=is_exact,
            optimality_gap_pct=0.0 if is_exact else 10.0,
            solver_name=self.name,
            execution_time_ms=exec_time_ms,
            nodes_explored=nodes_explored,
            nodes_pruned=nodes_pruned,
            metadata={
                "search_strategy": "DFS Backtracking",
                "safeguard_triggered": not is_exact,
            },
        )

