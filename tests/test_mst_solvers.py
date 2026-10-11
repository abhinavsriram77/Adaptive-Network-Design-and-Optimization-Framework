"""Comprehensive unit tests for MST solvers (DSU, Kruskal, Prim Heap, Prim Dense)."""

import math
import sys
from pathlib import Path

# Ensure project root is in sys.path
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import pytest
from algorithms.mst.base import GraphDisconnectedError
from algorithms.mst.disjoint_set import DisjointSetUnion
from algorithms.mst.kruskal import KruskalMST
from algorithms.mst.prim import PrimDenseMST, PrimHeapMST
from core.edge import NetworkEdge
from core.graph import NetworkGraph
from core.node import DataCenter, IoTGateway, NetworkHub
from utils.generator import generate_random_network


def test_disjoint_set_union_operations():
    dsu = DisjointSetUnion(["A", "B", "C", "D", "E"])
    assert dsu.sets_count == 5

    # Union A and B
    assert dsu.union("A", "B") is True
    assert dsu.sets_count == 4
    assert dsu.connected("A", "B") is True
    assert dsu.connected("A", "C") is False

    # Attempt union on already connected pair
    assert dsu.union("A", "B") is False
    assert dsu.sets_count == 4

    # Union C and D, then B and D
    assert dsu.union("C", "D") is True
    assert dsu.union("B", "D") is True
    assert dsu.sets_count == 2
    assert dsu.connected("A", "D") is True
    assert dsu.connected("A", "C") is True

    # Check path compression telemetry
    _ = dsu.find("C")
    assert dsu.find_ops > 0
    assert dsu.compressions >= 0

    comps = dsu.get_components()
    assert len(comps) == 2


def build_sample_connected_graph() -> NetworkGraph:
    """Build a classic 6-node weighted graph.
    
    Vertices: 0, 1, 2, 3, 4, 5
    Edges with known unique weights so MST is unique.
    """
    g = NetworkGraph(directed=False)
    for i in range(6):
        g.add_node(NetworkHub(id=f"n{i}", name=f"Node {i}"))

    # Edges: (u, v, weight)
    edges = [
        ("n0", "n1", 4.0),
        ("n0", "n2", 2.0),
        ("n1", "n2", 4.0),
        ("n1", "n3", 3.0),
        ("n2", "n3", 2.0),
        ("n2", "n4", 4.0),
        ("n3", "n4", 3.0),
        ("n3", "n5", 5.0),
        ("n4", "n5", 1.0),
    ]
    for u, v, w in edges:
        g.add_edge(NetworkEdge(u=u, v=v, weight=w))

    return g


def test_mst_equivalence_across_solvers():
    graph = build_sample_connected_graph()
    kruskal = KruskalMST()
    prim_heap = PrimHeapMST()
    prim_dense = PrimDenseMST()

    res_kruskal = kruskal.solve(graph)
    res_prim_heap = prim_heap.solve(graph)
    res_prim_dense = prim_dense.solve(graph)

    # Required edges for spanning tree = |V| - 1 = 6 - 1 = 5
    assert len(res_kruskal.edges) == 5
    assert len(res_prim_heap.edges) == 5
    assert len(res_prim_dense.edges) == 5

    # Known MST edges for this graph:
    # (n4, n5, 1.0), (n0, n2, 2.0), (n2, n3, 2.0), (n1, n3, 3.0), (n3, n4, 3.0) -> total = 11.0
    expected_weight = 11.0
    assert math.isclose(res_kruskal.total_weight, expected_weight)
    assert math.isclose(res_prim_heap.total_weight, expected_weight)
    assert math.isclose(res_prim_dense.total_weight, expected_weight)

    assert res_kruskal.is_spanning_tree is True
    assert res_prim_heap.is_spanning_tree is True
    assert res_prim_dense.is_spanning_tree is True

    assert res_kruskal.spanned_nodes() == {"n0", "n1", "n2", "n3", "n4", "n5"}
    assert res_prim_heap.spanned_nodes() == {"n0", "n1", "n2", "n3", "n4", "n5"}
    assert res_prim_dense.spanned_nodes() == {"n0", "n1", "n2", "n3", "n4", "n5"}


def test_mst_trivial_graphs():
    solvers = [KruskalMST(), PrimHeapMST(), PrimDenseMST()]

    # Empty graph
    g_empty = NetworkGraph(directed=False)
    for solver in solvers:
        res = solver.solve(g_empty)
        assert res.total_weight == 0.0
        assert len(res.edges) == 0

    # Single-node graph
    g_single = NetworkGraph(directed=False)
    g_single.add_node(NetworkHub(id="solo", name="Solo"))
    for solver in solvers:
        res = solver.solve(g_single)
        assert res.total_weight == 0.0
        assert len(res.edges) == 0
        assert res.is_spanning_tree is True


def test_mst_disconnected_graph_handling():
    g = NetworkGraph(directed=False)
    g.add_node(NetworkHub(id="A", name="A"))
    g.add_node(NetworkHub(id="B", name="B"))
    g.add_node(NetworkHub(id="C", name="C"))
    g.add_node(NetworkHub(id="D", name="D"))

    # Component 1: A-B
    g.add_edge(NetworkEdge(u="A", v="B", weight=5.0))
    # Component 2: C-D
    g.add_edge(NetworkEdge(u="C", v="D", weight=3.0))

    solvers = [KruskalMST(), PrimHeapMST(), PrimDenseMST()]

    for solver in solvers:
        # Default allow_forest=False must raise GraphDisconnectedError
        with pytest.raises(GraphDisconnectedError):
            solver.solve(g, allow_forest=False)

        # allow_forest=True must succeed, returning Minimum Spanning Forest
        res_forest = solver.solve(g, allow_forest=True)
        assert res_forest.is_spanning_tree is False
        assert res_forest.components_count == 2
        assert len(res_forest.edges) == 2
        assert math.isclose(res_forest.total_weight, 8.0)


def test_random_synthetic_graphs_equivalence():
    """Verify Kruskal and Prim produce identical total MST weight across 5 randomized topologies."""
    for seed in range(42, 47):
        g = generate_random_network(num_nodes=25, density=0.25, ensure_connected=True, seed=seed)
        assert g.is_connected()

        kruskal_res = KruskalMST().solve(g)
        prim_heap_res = PrimHeapMST().solve(g)
        prim_dense_res = PrimDenseMST().solve(g)

        assert len(kruskal_res.edges) == 24
        assert len(prim_heap_res.edges) == 24
        assert len(prim_dense_res.edges) == 24

        # All solvers must yield identical total weight
        assert math.isclose(kruskal_res.total_weight, prim_heap_res.total_weight, rel_tol=1e-5)
        assert math.isclose(prim_heap_res.total_weight, prim_dense_res.total_weight, rel_tol=1e-5)


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
