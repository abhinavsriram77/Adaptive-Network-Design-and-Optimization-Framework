"""Unit tests for the Adaptive MST Selector and dynamic dispatch engine."""

import math
import sys
from pathlib import Path

# Ensure project root is in sys.path
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import pytest
from algorithms.mst.base import GraphDisconnectedError
from algorithms.mst.selector import AdaptiveMSTSelector
from utils.generator import generate_random_network


def test_adaptive_selector_sparse_dispatch():
    selector = AdaptiveMSTSelector(density_threshold=0.35, dense_node_threshold=40)
    # Generate sparse topology (density ~0.15)
    sparse_g = generate_random_network(num_nodes=30, density=0.15, ensure_connected=True, seed=101)

    solver, rationale = selector.select_algorithm(sparse_g)
    assert "Kruskal" in solver.name
    assert "Sparse topology detected" in rationale

    result = selector.solve(sparse_g)
    assert "Kruskal" in result.algorithm_name
    assert result.is_spanning_tree is True
    assert len(result.edges) == 29
    assert "selection_rationale" in result.metadata
    assert "selector_overhead_ms" in result.metadata


def test_adaptive_selector_dense_large_scale_dispatch():
    selector = AdaptiveMSTSelector(density_threshold=0.35, dense_node_threshold=40)
    # Generate dense graph with |V| = 45 (>= 40) and density = 0.60 (>= 0.35)
    dense_g = generate_random_network(num_nodes=45, density=0.60, ensure_connected=True, seed=202)

    solver, rationale = selector.select_algorithm(dense_g)
    assert "Dense Matrix" in solver.name
    assert "Dense high-order topology detected" in rationale

    result = selector.solve(dense_g)
    assert "Dense Matrix" in result.algorithm_name
    assert result.is_spanning_tree is True
    assert len(result.edges) == 44


def test_adaptive_selector_dense_small_scale_dispatch():
    selector = AdaptiveMSTSelector(density_threshold=0.35, dense_node_threshold=40)
    # Generate dense graph with |V| = 15 (< 40) and density = 0.50 (>= 0.35)
    dense_small_g = generate_random_network(num_nodes=15, density=0.50, ensure_connected=True, seed=303)

    solver, rationale = selector.select_algorithm(dense_small_g)
    assert "Binary Min-Heap" in solver.name
    assert "Dense small-scale topology detected" in rationale

    result = selector.solve(dense_small_g)
    assert "Binary Min-Heap" in result.algorithm_name
    assert len(result.edges) == 14


def test_adaptive_selector_forced_algorithm_override():
    selector = AdaptiveMSTSelector()
    sparse_g = generate_random_network(num_nodes=20, density=0.20, ensure_connected=True, seed=404)

    # Force Prim Dense on sparse graph
    res_forced = selector.solve(sparse_g, force_algorithm="prim_dense")
    assert "Dense Matrix" in res_forced.algorithm_name
    assert len(res_forced.edges) == 19

    # Force invalid algorithm
    with pytest.raises(ValueError):
        selector.solve(sparse_g, force_algorithm="non_existent_solver")


def test_adaptive_selector_threshold_customization():
    # If density threshold is configured to 0.10, a graph with density 0.20 should be treated as dense
    selector = AdaptiveMSTSelector(density_threshold=0.10, dense_node_threshold=10)
    graph = generate_random_network(num_nodes=15, density=0.20, ensure_connected=True, seed=505)

    solver, _ = selector.select_algorithm(graph)
    assert "Dense Matrix" in solver.name


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
