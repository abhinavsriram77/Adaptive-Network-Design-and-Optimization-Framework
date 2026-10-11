"""Cost matrix reduction engine for calculating admissible TSP lower bounds."""

from __future__ import annotations

import math
from typing import List, Tuple


class ReducedMatrix:
    """Utility engine managing row/column matrix reduction and incremental lower bounds."""

    @staticmethod
    def reduce_matrix(matrix: List[List[float]]) -> Tuple[List[List[float]], float]:
        """Perform full row and column reduction on a cost matrix.
        
        Args:
            matrix: Square n x n float cost matrix.
            
        Returns:
            Tuple of (reduced_matrix: 2D float list, reduction_cost: float).
        """
        n = len(matrix)
        reduced = [row[:] for row in matrix]
        reduction_cost = 0.0

        # 1. Row reduction: subtract row minimum from each non-infinite cell
        for i in range(n):
            row_min = math.inf
            for j in range(n):
                if reduced[i][j] < row_min:
                    row_min = reduced[i][j]

            if row_min != math.inf and row_min > 0.0:
                reduction_cost += row_min
                for j in range(n):
                    if reduced[i][j] != math.inf:
                        reduced[i][j] -= row_min

        # 2. Column reduction: subtract column minimum from each non-infinite cell
        for j in range(n):
            col_min = math.inf
            for i in range(n):
                if reduced[i][j] < col_min:
                    col_min = reduced[i][j]

            if col_min != math.inf and col_min > 0.0:
                reduction_cost += col_min
                for i in range(n):
                    if reduced[i][j] != math.inf:
                        reduced[i][j] -= col_min

        return reduced, reduction_cost

    @staticmethod
    def create_child_matrix(
        parent_matrix: List[List[float]],
        parent_lb: float,
        u: int,
        v: int,
        start_node: int = 0,
        is_final_step: bool = False,
    ) -> Tuple[List[List[float]], float]:
        """Generate child reduced matrix and lower bound when appending edge (u, v).
        
        Args:
            parent_matrix: Reduced matrix of parent search node.
            parent_lb: Lower bound of parent search node.
            u: Source node index of the chosen step.
            v: Destination node index of the chosen step.
            start_node: Origin depot index (default 0).
            is_final_step: True if this edge connects the last visited site back to the depot.
            
        Returns:
            Tuple of (child_reduced_matrix, child_lower_bound).
        """
        n = len(parent_matrix)
        child_matrix = [row[:] for row in parent_matrix]

        # The cost of traversing edge (u, v) in the parent's reduced frame
        edge_cost = parent_matrix[u][v]
        if edge_cost == math.inf:
            return child_matrix, math.inf

        # 1. Row u cannot be used again
        for j in range(n):
            child_matrix[u][j] = math.inf

        # 2. Column v cannot be used again
        for i in range(n):
            child_matrix[i][v] = math.inf

        # 3. Prevent premature cycle back to start node unless it's the final closure step
        if not is_final_step:
            child_matrix[v][start_node] = math.inf
            # Prevent immediate return edge (v, u)
            child_matrix[v][u] = math.inf

        # 4. Re-reduce the modified child matrix
        reduced, reduction_cost = ReducedMatrix.reduce_matrix(child_matrix)
        child_lb = parent_lb + edge_cost + reduction_cost

        return reduced, child_lb

