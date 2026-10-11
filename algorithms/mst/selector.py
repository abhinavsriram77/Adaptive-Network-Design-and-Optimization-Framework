"""Adaptive Minimum Spanning Tree Selector Engine.

Dynamically inspects topological density D(G) and vertex scaling |V| to dispatch
the mathematically optimal MST algorithm (Kruskal with DSU vs. Prim Heap vs. Prim Dense).
"""

from __future__ import annotations

import time
from typing import Dict, Optional, Tuple

from algorithms.mst.base import BaseMSTSolver, MSTResult
from algorithms.mst.kruskal import KruskalMST
from algorithms.mst.prim import PrimDenseMST, PrimHeapMST
from core.graph import NetworkGraph


class AdaptiveMSTSelector:
    """Intelligent dispatch engine selecting MST algorithms based on graph characteristics.
    
    Attributes:
        density_threshold: Critical density theta partitioning sparse and dense regimes (default 0.35).
        dense_node_threshold: Vertex scale above which dense matrix Prim strictly dominates (default 40).
    """

    def __init__(
        self,
        density_threshold: float = 0.35,
        dense_node_threshold: int = 40,
    ) -> None:
        if not (0.0 < density_threshold < 1.0):
            raise ValueError(f"density_threshold must be strictly between 0.0 and 1.0, got: {density_threshold}")
        if dense_node_threshold < 2:
            raise ValueError(f"dense_node_threshold must be >= 2, got: {dense_node_threshold}")

        self.density_threshold = density_threshold
        self.dense_node_threshold = dense_node_threshold

        self._solvers: Dict[str, BaseMSTSolver] = {
            "kruskal": KruskalMST(),
            "prim_heap": PrimHeapMST(),
            "prim_dense": PrimDenseMST(),
        }

    def select_algorithm(self, graph: NetworkGraph) -> Tuple[BaseMSTSolver, str]:
        """Determine the optimal MST algorithm based on graph density and scale.
        
        Args:
            graph: The NetworkGraph to evaluate.
            
        Returns:
            Tuple of (Selected Solver Instance, Rationale Description).
        """
        d = graph.density()
        v = graph.num_nodes
        e = graph.num_edges

        # Trivial or sparse graph
        if d < self.density_threshold:
            solver = self._solvers["kruskal"]
            rationale = (
                f"Sparse topology detected (Density D={d:.4f} < {self.density_threshold}). "
                f"Kruskal's algorithm selected: O(|E| log |E|) edge sorting with Disjoint-Set Union "
                f"is optimal for low edge counts (|E|={e}, |V|={v})."
            )
            return solver, rationale

        # Dense graph with significant vertex count
        if v >= self.dense_node_threshold:
            solver = self._solvers["prim_dense"]
            rationale = (
                f"Dense high-order topology detected (Density D={d:.4f} >= {self.density_threshold}, |V|={v} >= {self.dense_node_threshold}). "
                f"Prim's Dense Matrix algorithm selected: strictly O(|V|²) operations avoid "
                f"the logarithmic overhead of edge sorting or priority queues on {e} edges."
            )
            return solver, rationale

        # Dense graph with small vertex count
        solver = self._solvers["prim_heap"]
        rationale = (
            f"Dense small-scale topology detected (Density D={d:.4f} >= {self.density_threshold}, |V|={v} < {self.dense_node_threshold}). "
            f"Prim's Heap algorithm selected: O(|E| log |V|) priority queue operations with small tree depth."
        )
        return solver, rationale

    def solve(
        self,
        graph: NetworkGraph,
        allow_forest: bool = False,
        force_algorithm: Optional[str] = None,
    ) -> MSTResult:
        """Execute the dynamically selected (or forced) MST algorithm.
        
        Args:
            graph: NetworkGraph to optimize.
            allow_forest: Whether to permit minimum spanning forests on disconnected graphs.
            force_algorithm: Optional override ('kruskal', 'prim_heap', 'prim_dense').
            
        Returns:
            MSTResult with performance metrics and selection rationale.
        """
        t0 = time.perf_counter()

        if force_algorithm is not None:
            key = force_algorithm.lower()
            if key not in self._solvers:
                raise ValueError(
                    f"Unknown algorithm {force_algorithm!r}. Available: {list(self._solvers.keys())}"
                )
            solver = self._solvers[key]
            rationale = f"User explicitly forced algorithm: {solver.name}"
        else:
            solver, rationale = self.select_algorithm(graph)

        selector_overhead_ms = (time.perf_counter() - t0) * 1000.0

        # Run solver
        result = solver.solve(graph, allow_forest=allow_forest)

        # Attach selector metadata
        result.metadata.update({
            "graph_density": graph.density(),
            "graph_nodes": graph.num_nodes,
            "graph_edges": graph.num_edges,
            "selected_solver": solver.name,
            "selection_rationale": rationale,
            "selector_overhead_ms": selector_overhead_ms,
            "density_threshold": self.density_threshold,
        })

        return result
