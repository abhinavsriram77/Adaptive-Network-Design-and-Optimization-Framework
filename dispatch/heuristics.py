"""Heuristic TSP solvers: Nearest Neighbor greedy and 2-Opt local search."""

from __future__ import annotations

import math
from typing import List, Tuple


class NearestNeighborHeuristic:
    """Greedy Nearest Neighbor heuristic constructing an initial valid TSP tour in O(n^2)."""

    @staticmethod
    def construct_tour(distance_matrix: List[List[float]], start_idx: int = 0) -> Tuple[List[int], float]:
        """Construct a tour by repeatedly visiting the closest unvisited site.
        
        Args:
            distance_matrix: n x n cost matrix.
            start_idx: Origin depot index (default 0).
            
        Returns:
            Tuple of (tour_indices: List[int], total_cost: float).
        """
        n = len(distance_matrix)
        if n <= 1:
            return [0, 0], 0.0

        visited = [False] * n
        tour = [start_idx]
        visited[start_idx] = True
        curr = start_idx
        total_cost = 0.0

        for _ in range(n - 1):
            next_node = -1
            min_dist = math.inf

            for candidate in range(n):
                if not visited[candidate] and distance_matrix[curr][candidate] < min_dist:
                    min_dist = distance_matrix[curr][candidate]
                    next_node = candidate

            if next_node == -1 or min_dist == math.inf:
                # Disconnected graph or unreached node
                return [], math.inf

            visited[next_node] = True
            tour.append(next_node)
            total_cost += min_dist
            curr = next_node

        # Return to depot
        return_cost = distance_matrix[curr][start_idx]
        if return_cost == math.inf:
            return [], math.inf

        tour.append(start_idx)
        total_cost += return_cost

        return tour, total_cost


class TwoOptLocalSearch:
    """2-Opt edge-exchange heuristic iteratively untangling tour crossings to reach 2-optimality."""

    @staticmethod
    def optimize(
        tour: List[int],
        distance_matrix: List[List[float]],
        max_iterations: int = 500,
    ) -> Tuple[List[int], float]:
        """Optimize a closed tour using 2-opt edge reversal swaps.
        
        Args:
            tour: Initial closed tour [v_0, v_1, ..., v_n, v_0].
            distance_matrix: n x n travel cost matrix.
            max_iterations: Maximum passes over candidate edge pairs.
            
        Returns:
            Tuple of (optimized_tour: List[int], optimized_cost: float).
        """
        if len(tour) <= 3:
            cost = TwoOptLocalSearch.calculate_tour_cost(tour, distance_matrix)
            return tour, cost

        best_tour = tour[:]
        best_cost = TwoOptLocalSearch.calculate_tour_cost(best_tour, distance_matrix)
        n = len(best_tour) - 1  # Excluding redundant final depot entry
        epsilon = 1e-6

        iteration = 0
        improved = True

        while improved and iteration < max_iterations:
            improved = False
            iteration += 1

            for i in range(n - 1):
                for j in range(i + 2, n if i > 0 else n - 1):
                    candidate_tour = (
                        best_tour[: i + 1]
                        + list(reversed(best_tour[i + 1 : j + 1]))
                        + best_tour[j + 1 :]
                    )
                    candidate_cost = TwoOptLocalSearch.calculate_tour_cost(
                        candidate_tour, distance_matrix
                    )

                    if candidate_cost < best_cost - epsilon:
                        best_tour = candidate_tour
                        best_cost = candidate_cost
                        improved = True
                        break
                if improved:
                    break

        return best_tour, best_cost

    @staticmethod
    def calculate_tour_cost(tour: List[int], distance_matrix: List[List[float]]) -> float:
        """Calculate total closed tour length."""
        if not tour:
            return math.inf
        total = 0.0
        for i in range(len(tour) - 1):
            dist = distance_matrix[tour[i]][tour[i + 1]]
            if dist == math.inf:
                return math.inf
            total += dist
        return total
