"""Unit tests for Floyd-Warshall all-pairs routing and path reconstruction."""

import math
import sys
from pathlib import Path

# Add project root to sys.path
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import pytest
from algorithms.routing.base import NegativeCycleError
from algorithms.routing.floyd_warshall import FloydWarshallRouter
from core.edge import NetworkEdge
from core.graph import NetworkGraph
from core.node import DataCenter, IoTGateway, NetworkHub


def build_routing_topology() -> NetworkGraph:
    """Build a 5-node test graph with known path distances.
    
    Nodes: A, B, C, D, E
    Edges:
      A - B (lat=2.0, bw=100.0)
      B - C (lat=3.0, bw=40.0)
      A - C (lat=6.0, bw=10.0)
      C - D (lat=1.0, bw=40.0)
      D - E (lat=4.0, bw=20.0)
      B - E (lat=10.0, bw=10.0)
    """
    g = NetworkGraph(directed=False)
    g.add_node(NetworkHub(id="A", name="Hub A"))
    g.add_node(NetworkHub(id="B", name="Hub B"))
    g.add_node(DataCenter(id="C", name="DC C"))
    g.add_node(NetworkHub(id="D", name="Hub D"))
    g.add_node(IoTGateway(id="E", name="Gateway E"))

    edges = [
        ("A", "B", 2.0, 100.0),
        ("B", "C", 3.0, 40.0),
        ("A", "C", 6.0, 10.0),
        ("C", "D", 1.0, 40.0),
        ("D", "E", 4.0, 20.0),
        ("B", "E", 10.0, 10.0),
    ]
    for u, v, lat, bw in edges:
        g.add_edge(NetworkEdge(u=u, v=v, weight=lat, latency_ms=lat, bandwidth_gbps=bw))

    return g


def test_floyd_warshall_pairwise_distances():
    g = build_routing_topology()
    router = FloydWarshallRouter(metric="latency_ms")
    result = router.compute_routing(g)

    # Known shortest path latencies:
    # A to A: 0
    # A to B: 2.0
    # A to C: min(6, 2+3) = 5.0 (path: A -> B -> C)
    # A to D: A -> B -> C -> D = 2 + 3 + 1 = 6.0
    # A to E: min(A -> B -> E (12.0), A -> B -> C -> D -> E (10.0)) = 10.0
    assert result.get_distance("A", "A") == 0.0
    assert result.get_distance("A", "B") == 2.0
    assert result.get_distance("A", "C") == 5.0
    assert result.get_distance("A", "D") == 6.0
    assert result.get_distance("A", "E") == 10.0

    # Path reconstruction
    path_ae = router.get_path(g, result, "A", "E")
    assert path_ae.exists is True
    assert path_ae.path == ["A", "B", "C", "D", "E"]
    assert path_ae.hop_count == 4
    assert math.isclose(path_ae.total_latency_ms, 10.0)
    # Bottleneck bandwidth along A-B(100), B-C(40), C-D(40), D-E(20) is 20.0
    assert path_ae.bottleneck_bandwidth_gbps == 20.0


def test_floyd_warshall_network_diameter_and_reachability():
    g = build_routing_topology()
    router = FloydWarshallRouter(metric="latency_ms")
    result = router.compute_routing(g)

    # All nodes are connected
    assert result.reachability_ratio() == 1.0
    # Diameter is maximum shortest path between any pair (A-E is 10.0, B-E via D is 8.0, C-E is 5.0)
    assert result.network_diameter() == 10.0


def test_floyd_warshall_disconnected_graph():
    g = NetworkGraph(directed=False)
    g.add_node(NetworkHub(id="A", name="A"))
    g.add_node(NetworkHub(id="B", name="B"))
    g.add_node(NetworkHub(id="C", name="C"))

    g.add_edge(NetworkEdge(u="A", v="B", weight=3.0, latency_ms=3.0))

    router = FloydWarshallRouter(metric="latency_ms")
    res = router.compute_routing(g)

    assert res.get_distance("A", "B") == 3.0
    assert res.get_distance("A", "C") == math.inf
    assert res.reachability_ratio() < 1.0

    path_ac = router.get_path(g, res, "A", "C")
    assert path_ac.exists is False
    assert path_ac.path == []
    assert path_ac.distance == math.inf


def test_floyd_warshall_negative_cycle_detection():
    # Direct adjacency matrix manipulation for negative cycle test
    # Note: NetworkEdge enforces weight >= 0 for physical links, but we can verify detection directly
    g = NetworkGraph(directed=True)
    g.add_node(NetworkHub(id="X", name="X"))
    g.add_node(NetworkHub(id="Y", name="Y"))
    g.add_edge(NetworkEdge(u="X", v="Y", weight=1.0, latency_ms=1.0, directed=True))
    g.add_edge(NetworkEdge(u="Y", v="X", weight=2.0, latency_ms=2.0, directed=True))

    router = FloydWarshallRouter(metric="latency_ms")
    res = router.compute_routing(g)
    assert res.has_negative_cycle is False


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
