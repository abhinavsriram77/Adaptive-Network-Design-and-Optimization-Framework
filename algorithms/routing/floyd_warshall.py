"""Floyd-Warshall Dynamic Programming All-Pairs Shortest Path Solver.

Computes full-mesh shortest communication paths, path reconstruction matrices,
and detects negative-weight cycles in Theta(|V|^3) operations.
"""

from __future__ import annotations

import math
import time
from typing import Dict, List, Optional, Tuple

from algorithms.routing.base import NegativeCycleError, PathInfo, RoutingResult
from core.graph import NetworkGraph


class FloydWarshallRouter:
    """All-pairs routing engine utilizing the Floyd-Warshall dynamic programming algorithm.
    
    Attributes:
        metric: Edge weight attribute to optimize ("latency_ms", "weight", etc.).
    """

    def __init__(self, metric: str = "latency_ms") -> None:
        self.metric = metric

    def compute_routing(self, graph: NetworkGraph) -> RoutingResult:
        """Compute the all-pairs shortest paths across the network graph.
        
        Args:
            graph: The NetworkGraph instance.
            
        Returns:
            RoutingResult containing distance and next-hop path reconstruction matrices.
            
        Raises:
            NegativeCycleError: If a negative cycle is detected along any path.
        """
        start_time = time.perf_counter()
        node_ids, matrix = graph.to_adjacency_matrix(metric=self.metric)
        n = len(node_ids)

        # 1. Initialize Distance matrix D and Next-Hop matrix
        d_matrix: List[List[float]] = [row[:] for row in matrix]
        next_hop: List[List[Optional[int]]] = [[None] * n for _ in range(n)]

        for i in range(n):
            for j in range(n):
                if i == j:
                    next_hop[i][j] = i
                elif d_matrix[i][j] != math.inf:
                    next_hop[i][j] = j

        comparisons = 0
        relaxations = 0

        # 2. Triple-nested Floyd-Warshall DP relaxation loop: Theta(n^3)
        for k in range(n):
            d_k = d_matrix[k]
            for i in range(n):
                d_ik = d_matrix[i][k]
                if d_ik == math.inf:
                    # Prune inner loop if path from i to k does not exist
                    comparisons += n
                    continue

                d_i = d_matrix[i]
                next_i = next_hop[i]

                for j in range(n):
                    comparisons += 1
                    d_kj = d_k[j]
                    if d_kj != math.inf:
                        new_dist = d_ik + d_kj
                        if new_dist < d_i[j]:
                            d_i[j] = new_dist
                            next_i[j] = next_i[k]
                            relaxations += 1

        # 3. Negative Cycle Detection: check for negative entries along the diagonal
        for i in range(n):
            if d_matrix[i][i] < 0.0:
                raise NegativeCycleError(
                    f"Negative weight cycle detected traversing node {node_ids[i]!r} (D[{i}][{i}] = {d_matrix[i][i]})."
                )

        exec_time_ms = (time.perf_counter() - start_time) * 1000.0

        return RoutingResult(
            node_ids=node_ids,
            distance_matrix=d_matrix,
            next_hop_matrix=next_hop,
            execution_time_ms=exec_time_ms,
            relaxations_count=relaxations,
            comparisons_count=comparisons,
            metric_used=self.metric,
            has_negative_cycle=False,
            metadata={
                "nodes_count": n,
                "edges_count": graph.num_edges,
                "density": graph.density(),
            },
        )

    def get_path(
        self, graph: NetworkGraph, routing_result: RoutingResult, source: str, target: str
    ) -> PathInfo:
        """Reconstruct the concrete shortest path between source and target with link attributes.
        
        Args:
            graph: The network graph topology.
            routing_result: Previously computed RoutingResult.
            source: Source node ID.
            target: Destination node ID.
            
        Returns:
            PathInfo containing the traversed path, total latency, and bottleneck bandwidth.
        """
        if not graph.has_node(source):
            raise KeyError(f"Source node {source!r} not found in graph.")
        if not graph.has_node(target):
            raise KeyError(f"Target node {target!r} not found in graph.")

        if source == target:
            return PathInfo(
                source=source,
                target=target,
                distance=0.0,
                path=[source],
                hop_count=0,
                total_latency_ms=0.0,
                bottleneck_bandwidth_gbps=math.inf,
                exists=True,
            )

        u_idx = routing_result._id_to_idx[source]
        v_idx = routing_result._id_to_idx[target]

        dist = routing_result.distance_matrix[u_idx][v_idx]
        if dist == math.inf:
            return PathInfo(
                source=source,
                target=target,
                distance=math.inf,
                path=[],
                hop_count=0,
                total_latency_ms=math.inf,
                bottleneck_bandwidth_gbps=0.0,
                exists=False,
            )

        idx_path = routing_result.reconstruct_path_indices(u_idx, v_idx)
        if not idx_path or idx_path[-1] != v_idx:
            return PathInfo(
                source=source,
                target=target,
                distance=math.inf,
                path=[],
                hop_count=0,
                total_latency_ms=math.inf,
                bottleneck_bandwidth_gbps=0.0,
                exists=False,
            )

        path_nodes = [routing_result.node_ids[idx] for idx in idx_path]

        # Aggregate path telemetry metrics
        total_lat = 0.0
        min_bw = math.inf

        for step in range(len(path_nodes) - 1):
            u_id = path_nodes[step]
            v_id = path_nodes[step + 1]
            edge = graph.get_edge(u_id, v_id)
            if edge is not None:
                total_lat += edge.latency_ms
                if edge.bandwidth_gbps < min_bw:
                    min_bw = edge.bandwidth_gbps

        return PathInfo(
            source=source,
            target=target,
            distance=dist,
            path=path_nodes,
            hop_count=len(path_nodes) - 1,
            total_latency_ms=total_lat,
            bottleneck_bandwidth_gbps=min_bw if min_bw != math.inf else 0.0,
            exists=True,
        )

    def all_pair_communication_costs(
        self, routing_result: RoutingResult
    ) -> Dict[Tuple[str, str], float]:
        """Generate a flattened mapping of all pair-to-pair communication costs."""
        costs: Dict[Tuple[str, str], float] = {}
        nodes = routing_result.node_ids
        for i, u in enumerate(nodes):
            for j, v in enumerate(nodes):
                if i != j:
                    costs[(u, v)] = routing_result.distance_matrix[i][j]
        return costs
