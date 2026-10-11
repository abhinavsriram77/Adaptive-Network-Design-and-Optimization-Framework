"""Synthetic network graph generator for algorithmic benchmarks and stress tests.

Generates heterogeneous network topologies with precise edge density control.
"""

from __future__ import annotations

import random
from typing import Optional

from core.edge import NetworkEdge
from core.graph import NetworkGraph
from core.node import DataCenter, IoTGateway, NetworkHub, Node


def generate_random_network(
    num_nodes: int,
    density: float,
    ensure_connected: bool = True,
    seed: Optional[int] = None,
    directed: bool = False,
) -> NetworkGraph:
    """Generate a random network graph with controlled topological density.
    
    Args:
        num_nodes: Number of vertices |V| (must be >= 1).
        density: Target edge density in [0.0, 1.0].
        ensure_connected: If True, guarantees that the graph is connected (requires density >= 2/|V|).
        seed: Random generator seed for repeatable experiments.
        directed: Whether to construct a directed or undirected network.
        
    Returns:
        Populated NetworkGraph instance with heterogeneous node types.
    """
    if num_nodes < 1:
        raise ValueError(f"num_nodes must be >= 1, got {num_nodes}")
    if not (0.0 <= density <= 1.0):
        raise ValueError(f"density must be in [0.0, 1.0], got {density}")

    rng = random.Random(seed)
    graph = NetworkGraph(directed=directed)

    # 1. Instantiate heterogeneous nodes
    for i in range(num_nodes):
        node_id = f"node_{i:04d}"
        role_selector = i % 3
        lat = rng.uniform(25.0, 48.0)
        lon = rng.uniform(-125.0, -70.0)

        node: Node
        if role_selector == 0:
            node = NetworkHub(
                id=node_id,
                name=f"Hub-{i}",
                latitude=lat,
                longitude=lon,
                switching_capacity_gbps=rng.choice([100.0, 400.0, 800.0]),
                max_connected_ports=rng.choice([32, 64, 128]),
            )
        elif role_selector == 1:
            node = DataCenter(
                id=node_id,
                name=f"DC-{i}",
                latitude=lat,
                longitude=lon,
                server_rack_count=rng.randint(50, 300),
                storage_capacity_tb=rng.uniform(500.0, 5000.0),
                tier_rating=rng.randint(2, 4),
            )
        else:
            node = IoTGateway(
                id=node_id,
                name=f"GW-{i}",
                latitude=lat,
                longitude=lon,
                sensor_channel_count=rng.randint(8, 64),
                battery_powered=(rng.random() > 0.5),
                battery_level_pct=rng.uniform(20.0, 100.0),
            )
        graph.add_node(node)

    if num_nodes <= 1:
        return graph

    # Compute target edge count
    max_edges = num_nodes * (num_nodes - 1)
    if not directed:
        max_edges //= 2

    target_edges = int(round(density * max_edges))

    # All candidate pairs
    all_pairs = []
    for i in range(num_nodes):
        for j in range(num_nodes):
            if directed:
                if i != j:
                    all_pairs.append((f"node_{i:04d}", f"node_{j:04d}"))
            else:
                if i < j:
                    all_pairs.append((f"node_{i:04d}", f"node_{j:04d}"))

    edges_added = set()

    # If connected is required, build an initial spanning tree
    if ensure_connected and num_nodes > 1:
        node_ids = [f"node_{i:04d}" for i in range(num_nodes)]
        rng.shuffle(node_ids)
        for i in range(1, num_nodes):
            # Connect current node to an already connected node
            u = node_ids[i]
            v = rng.choice(node_ids[:i])
            pair = (u, v) if directed else ((u, v) if u <= v else (v, u))
            edges_added.add(pair)
            w = rng.uniform(1.0, 100.0)
            lat = rng.uniform(0.5, 25.0)
            bw = rng.choice([10.0, 40.0, 100.0])
            graph.add_edge(
                NetworkEdge(
                    u=u,
                    v=v,
                    weight=round(w, 2),
                    latency_ms=round(lat, 2),
                    bandwidth_gbps=bw,
                    directed=directed,
                )
            )

    # Fill remaining edges until reaching target_edges
    rng.shuffle(all_pairs)
    for u, v in all_pairs:
        if len(edges_added) >= target_edges:
            break
        pair = (u, v) if directed else ((u, v) if u <= v else (v, u))
        if pair not in edges_added:
            edges_added.add(pair)
            w = rng.uniform(1.0, 100.0)
            lat = rng.uniform(0.5, 25.0)
            bw = rng.choice([10.0, 40.0, 100.0])
            graph.add_edge(
                NetworkEdge(
                    u=u,
                    v=v,
                    weight=round(w, 2),
                    latency_ms=round(lat, 2),
                    bandwidth_gbps=bw,
                    directed=directed,
                )
            )

    return graph
