"""Kruskal's Minimum Spanning Tree algorithm implementation.

Employs Disjoint-Set Union with Rank Heuristic and Path Compression.
Optimal for sparse graphs where |E| << |V|^2, achieving O(|E| log |E|) time complexity.
"""

from __future__ import annotations

import time
from typing import List

from algorithms.mst.base import BaseMSTSolver, GraphDisconnectedError, MSTResult
from algorithms.mst.disjoint_set import DisjointSetUnion
from core.edge import NetworkEdge
from core.graph import NetworkGraph


class KruskalMST(BaseMSTSolver):
    """Kruskal's algorithm for computing Minimum Spanning Trees and Forests."""

    @property
    def name(self) -> str:
        return "Kruskal's Algorithm (DSU with Rank & Path Compression)"

    def solve(self, graph: NetworkGraph, allow_forest: bool = False) -> MSTResult:
        """Execute Kruskal's algorithm on the given network graph.
        
        Args:
            graph: The NetworkGraph instance.
            allow_forest: Whether to permit disconnected spanning forests.
            
        Returns:
            MSTResult detailing selected backbone links and runtime telemetry.
            
        Raises:
            GraphDisconnectedError: If the graph is disconnected and allow_forest is False.
        """
        start_time = time.perf_counter()
        nodes = graph.get_all_nodes()
        node_count = len(nodes)

        # Trivial cases: empty or single-node topology
        if node_count <= 1:
            exec_time = (time.perf_counter() - start_time) * 1000.0
            return MSTResult(
                edges=[],
                total_weight=0.0,
                execution_time_ms=exec_time,
                operations_count=0,
                algorithm_name=self.name,
                is_spanning_tree=True,
                components_count=node_count,
                metadata={"edges_evaluated": 0, "edges_discarded": 0},
            )

        # Initialize DSU with all node IDs
        dsu = DisjointSetUnion(node.id for node in nodes)

        edges = graph.get_all_edges()
        sort_start = time.perf_counter()
        sorted_edges = sorted(edges)
        sort_time_ms = (time.perf_counter() - sort_start) * 1000.0

        # Estimated comparisons during TimSort: ~ |E| * log2(|E|)
        e_len = len(sorted_edges)
        comparison_ops = int(e_len * (e_len.bit_length() - 1)) if e_len > 1 else 0

        mst_edges: List[NetworkEdge] = []
        total_weight: float = 0.0
        edges_discarded: int = 0
        edges_evaluated: int = 0
        target_edges = node_count - 1

        for edge in sorted_edges:
            edges_evaluated += 1
            if dsu.union(edge.u, edge.v):
                mst_edges.append(edge)
                total_weight += edge.weight
                # Early termination when a single spanning tree is fully formed
                if len(mst_edges) == target_edges:
                    break
            else:
                edges_discarded += 1

        components = dsu.sets_count
        is_single_tree = (components == 1)

        if not is_single_tree and not allow_forest:
            raise GraphDisconnectedError(
                f"Graph is disconnected into {components} partitions. Kruskal cannot form a single MST "
                f"(selected {len(mst_edges)}/{target_edges} required edges). Set allow_forest=True to obtain MSF."
            )

        exec_time = (time.perf_counter() - start_time) * 1000.0
        total_ops = comparison_ops + dsu.find_ops + dsu.union_ops

        return MSTResult(
            edges=mst_edges,
            total_weight=total_weight,
            execution_time_ms=exec_time,
            operations_count=total_ops,
            algorithm_name=self.name,
            is_spanning_tree=is_single_tree,
            components_count=components,
            metadata={
                "edges_evaluated": edges_evaluated,
                "edges_discarded": edges_discarded,
                "sort_time_ms": sort_time_ms,
                "dsu_find_ops": dsu.find_ops,
                "dsu_union_ops": dsu.union_ops,
                "dsu_compressions": dsu.compressions,
            },
        )
