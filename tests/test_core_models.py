"""Unit tests for core models (Node, NetworkEdge, NetworkGraph)."""

from core.graph import NetworkGraph
from core.edge import NetworkEdge
from core.node import Node, NodeType, NetworkHub, DataCenter, IoTGateway
import pytest
import math
import sys
from pathlib import Path

# Ensure project root is on sys.path for direct script execution
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)


def test_node_initialization_and_validation():
    hub = NetworkHub(
        id="hub-1",
        name="Central Hub",
        latitude=37.7749,
        longitude=-122.4194,
        switching_capacity_gbps=800.0,
        max_connected_ports=128,
    )
    assert hub.id == "hub-1"
    assert hub.node_type == NodeType.NETWORK_HUB
    assert hub.switching_capacity_gbps == 800.0
    assert hub.max_connected_ports == 128

    dc = DataCenter(
        id="dc-1",
        name="Primary DC",
        latitude=40.7128,
        longitude=-74.0060,
        server_rack_count=256,
        storage_capacity_tb=5000.0,
        tier_rating=4,
    )
    assert dc.node_type == NodeType.DATA_CENTER
    assert dc.tier_rating == 4

    iot = IoTGateway(
        id="iot-1",
        name="Gateway Edge",
        sensor_channel_count=32,
        battery_powered=True,
        battery_level_pct=85.5,
    )
    assert iot.node_type == NodeType.IOT_GATEWAY
    assert iot.battery_level_pct == 85.5

    # Validation errors
    with pytest.raises(ValueError):
        Node(id="", name="Invalid", node_type=NodeType.NETWORK_HUB)

    with pytest.raises(ValueError):
        Node(id="n1", name="Invalid Lat",
             node_type=NodeType.NETWORK_HUB, latitude=100.0)

    with pytest.raises(ValueError):
        DataCenter(id="dc-inv", name="Inv Tier", tier_rating=5)


def test_network_edge_initialization_and_behavior():
    e1 = NetworkEdge(u="hub-1", v="dc-1", weight=12.5,
                     latency_ms=4.2, bandwidth_gbps=100.0)
    e2 = NetworkEdge(u="dc-1", v="hub-1", weight=12.5,
                     latency_ms=4.2, bandwidth_gbps=100.0)

    # Undirected equality
    assert e1 == e2
    assert hash(e1) == hash(e2)
    assert e1.canonical_endpoints == ("dc-1", "hub-1")

    # Directed distinction
    e_dir1 = NetworkEdge(u="hub-1", v="dc-1", weight=12.5, directed=True)
    e_dir2 = NetworkEdge(u="dc-1", v="hub-1", weight=12.5, directed=True)
    assert e_dir1 != e_dir2

    # Validation checks
    with pytest.raises(ValueError):
        NetworkEdge(u="a", v="a", weight=5.0)  # Self loop

    with pytest.raises(ValueError):
        NetworkEdge(u="a", v="b", weight=-1.0)  # Negative weight


def test_network_graph_topology_and_density():
    g = NetworkGraph(directed=False)

    n1 = NetworkHub(id="A", name="Node A")
    n2 = NetworkHub(id="B", name="Node B")
    n3 = NetworkHub(id="C", name="Node C")
    n4 = NetworkHub(id="D", name="Node D")

    for n in [n1, n2, n3, n4]:
        g.add_node(n)

    assert g.num_nodes == 4
    assert g.num_edges == 0
    assert g.density() == 0.0
    assert not g.is_connected()

    # Add edges forming a triangle A-B-C and disconnected D
    g.add_edge(NetworkEdge(u="A", v="B", weight=2.0))
    g.add_edge(NetworkEdge(u="B", v="C", weight=3.0))
    g.add_edge(NetworkEdge(u="C", v="A", weight=4.0))

    assert g.num_edges == 3
    # Max undirected edges for 4 nodes is 4*3/2 = 6. Density = 3 / 6 = 0.5
    assert math.isclose(g.density(), 0.5)
    assert not g.is_connected()
    assert len(g.connected_components()) == 2

    # Connect D to complete connectivity
    g.add_edge(NetworkEdge(u="C", v="D", weight=1.5))
    assert g.is_connected()
    assert len(g.connected_components()) == 1
    # 4 edges out of 6 -> density = 4/6 = 0.6666...
    assert math.isclose(g.density(), 4.0 / 6.0)


def test_network_graph_matrix_generation():
    g = NetworkGraph(directed=False)
    g.add_node(NetworkHub(id="A", name="A"))
    g.add_node(NetworkHub(id="B", name="B"))
    g.add_node(NetworkHub(id="C", name="C"))

    g.add_edge(NetworkEdge(u="A", v="B", weight=5.0, latency_ms=10.0))
    g.add_edge(NetworkEdge(u="B", v="C", weight=7.0, latency_ms=15.0))

    node_ids, weight_matrix = g.to_adjacency_matrix(metric="weight")
    assert node_ids == ["A", "B", "C"]
    assert weight_matrix[0][0] == 0.0
    assert weight_matrix[0][1] == 5.0
    assert weight_matrix[1][0] == 5.0
    assert weight_matrix[0][2] == math.inf
    assert weight_matrix[1][2] == 7.0
    assert weight_matrix[2][1] == 7.0


def test_network_graph_parallel_edge_reduction():
    g = NetworkGraph(directed=False)
    g.add_node(NetworkHub(id="A", name="A"))
    g.add_node(NetworkHub(id="B", name="B"))

    # Add edge with higher weight
    g.add_edge(NetworkEdge(u="A", v="B", weight=10.0))
    assert g.get_edge("A", "B").weight == 10.0

    # Add edge with lower weight -> should replace/retain minimal
    g.add_edge(NetworkEdge(u="A", v="B", weight=4.0))
    assert g.get_edge("A", "B").weight == 4.0

    # Add edge with higher weight -> should be ignored
    g.add_edge(NetworkEdge(u="A", v="B", weight=8.0))
    assert g.get_edge("A", "B").weight == 4.0
    assert g.num_edges == 1


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
