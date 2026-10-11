"""Prim's Minimum Spanning Tree algorithm implementation.

Provides two specialized implementations:
1. PrimHeapMST: Priority Queue (Binary Min-Heap) operating over Adjacency List, O(|E| log |V|).
2. PrimDenseMST: Key Array operating over Adjacency Matrix, strictly O(|V|^2), ideal for dense graphs.
"""

from __future__ import annotations

import heapq
import math
import time
from typing import Dict, List, Optional, Set, Tuple

from algorithms.mst.base import BaseMSTSolver, GraphDisconnectedError, MSTResult
from core.edge import NetworkEdge
from core.graph import NetworkGraph


class PrimHeapMST(BaseMSTSolver):
    """Prim's algorithm using a binary min-heap over adjacency lists.
    
    Time Complexity:
        O(|E| log |V|) using priority queue.
    Space Complexity:
        O(|V| + |E|).
    """

    @property
    def name(self) -> str:
        return "Prim's Algorithm (Binary Min-Heap / Adjacency List)"

    def solve(self, graph: NetworkGraph, allow_forest: bool = False) -> MSTResult:
        start_time = time.perf_counter()
        nodes = graph.get_all_nodes()
        node_count = len(nodes)

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
            )

        visited: Set[str] = set()
        mst_edges: List[NetworkEdge] = []
        total_weight: float = 0.0
        operations: int = 0
        components: int = 0

        # We will loop across unvisited components
        all_node_ids = [n.id for n in nodes]
        for start_node in all_node_ids:
            if start_node in visited:
                continue

            components += 1
            if components > 1 and not allow_forest:
                raise GraphDisconnectedError(
                    f"Graph is disconnected. Prim cannot span all vertices without allow_forest=True."
                )

            visited.add(start_node)
            # Priority queue entries: (weight, latency, counter, u, v, edge)
            pq: List[Tuple[float, float, int, str, str, NetworkEdge]] = []
            heap_counter = 0

            # Push initial incident edges
            for nbr in graph.neighbors(start_node):
                edge = graph.get_edge(start_node, nbr)
                if edge is not None:
                    operations += 1
                    heap_counter += 1
                    heapq.heappush(pq, (edge.weight, edge.latency_ms, heap_counter, start_node, nbr, edge))

            while pq:
                w, lat, _, u, v, edge = heapq.heappop(pq)
                operations += 1

                # If destination node is already in tree, skip edge
                if v in visited:
                    continue

                visited.add(v)
                mst_edges.append(edge)
                total_weight += edge.weight

                # Add newly reachable edges from node v
                for nbr in graph.neighbors(v):
                    if nbr not in visited:
                        next_edge = graph.get_edge(v, nbr)
                        if next_edge is not None:
                            operations += 1
                            heap_counter += 1
                            heapq.heappush(
                                pq,
                                (next_edge.weight, next_edge.latency_ms, heap_counter, v, nbr, next_edge),
                            )

        is_single_tree = (components == 1 and len(visited) == node_count)
        if not is_single_tree and not allow_forest:
            raise GraphDisconnectedError(
                f"Graph is disconnected into {components} partitions. Only {len(visited)}/{node_count} nodes reached."
            )

        exec_time = (time.perf_counter() - start_time) * 1000.0
        return MSTResult(
            edges=mst_edges,
            total_weight=total_weight,
            execution_time_ms=exec_time,
            operations_count=operations,
            algorithm_name=self.name,
            is_spanning_tree=is_single_tree,
            components_count=components,
            metadata={"visited_nodes": len(visited), "heap_pushes": operations},
        )


class PrimDenseMST(BaseMSTSolver):
    """Prim's algorithm using direct key array over dense Adjacency Matrix.
    
    Time Complexity:
        Strictly O(|V|^2), avoiding priority queue logarithmic overhead on dense graphs.
    Space Complexity:
        O(|V|^2) for matrix representation.
    """

    @property
    def name(self) -> str:
        return "Prim's Algorithm (Dense Matrix O(|V|²))"

    def solve(self, graph: NetworkGraph, allow_forest: bool = False) -> MSTResult:
        start_time = time.perf_counter()
        node_ids, matrix = graph.to_adjacency_matrix(metric="weight")
        n = len(node_ids)

        if n <= 1:
            exec_time = (time.perf_counter() - start_time) * 1000.0
            return MSTResult(
                edges=[],
                total_weight=0.0,
                execution_time_ms=exec_time,
                operations_count=0,
                algorithm_name=self.name,
                is_spanning_tree=True,
                components_count=n,
            )

        idx_to_id = {i: node_ids[i] for i in range(n)}
        in_mst = [False] * n
        min_key = [math.inf] * n
        parent_idx = [-1] * n

        mst_edges: List[NetworkEdge] = []
        total_weight: float = 0.0
        operations: int = 0
        components: int = 0

        unvisited_count = n

        while unvisited_count > 0:
            # Find unvisited vertex with smallest key
            min_val = math.inf
            u = -1

            for i in range(n):
                operations += 1
                if not in_mst[i] and min_key[i] < min_val:
                    min_val = min_key[i]
                    u = i

            # If all reachable vertices from current component have been exhausted
            if u == -1:
                components += 1
                if components > 1 and not allow_forest:
                    raise GraphDisconnectedError(
                        f"Graph is disconnected. Dense Prim cannot span remaining {unvisited_count} vertices."
                    )
                # Pick next unvisited vertex as new component root
                for i in range(n):
                    if not in_mst[i]:
                        u = i
                        min_key[u] = 0.0
                        break

            in_mst[u] = True
            unvisited_count -= 1

            # If u has a valid parent, add the connecting edge to MST
            if parent_idx[u] != -1:
                p_id = idx_to_id[parent_idx[u]]
                u_id = idx_to_id[u]
                edge = graph.get_edge(p_id, u_id)
                if edge is not None:
                    mst_edges.append(edge)
                    total_weight += edge.weight

            # Update keys of all neighbors of u
            for v in range(n):
                operations += 1
                weight = matrix[u][v]
                if not in_mst[v] and weight < min_key[v]:
                    min_key[v] = weight
                    parent_idx[v] = u

        is_single_tree = (components == 1)
        exec_time = (time.perf_counter() - start_time) * 1000.0

        return MSTResult(
            edges=mst_edges,
            total_weight=total_weight,
            execution_time_ms=exec_time,
            operations_count=operations,
            algorithm_name=self.name,
            is_spanning_tree=is_single_tree,
            components_count=components,
            metadata={"matrix_dimension": n, "scanned_cells": operations},
        )
