"""Unit tests for TSP Field Dispatch, Matrix Reduction, Heuristics, and Adaptive Dispatch Engine."""

import itertools
import math
import random
import sys
from pathlib import Path

# Add project root to sys.path
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import pytest
from core.edge import NetworkEdge
from core.graph import NetworkGraph
from core.node import Node, NodeType
from dispatch.backtracking import BacktrackingTSPSolver
from dispatch.base import BaseTSPSolver, TourManifest
from dispatch.branch_and_bound import BranchAndBoundTSPSolver
from dispatch.heuristics import NearestNeighborHeuristic, TwoOptLocalSearch
from dispatch.reduced_matrix import ReducedMatrix
from dispatch.selector import AdaptiveDispatchEngine
from dispatch.site import DispatchSite


def test_dispatch_site_properties_and_validation():
    """Verify DispatchSite creation, property constraints, and dictionary serialization."""
    depot = DispatchSite(
        id="DEPOT-01",
        name="Central Maintenance Hub",
        latitude=37.7749,
        longitude=-122.4194,
        service_time_mins=0.0,
        is_depot=True,
    )
    assert depot.id == "DEPOT-01"
    assert depot.is_depot is True
    assert depot.service_time_mins == 0.0

    site = DispatchSite(
        id="SITE-A",
        name="Core Router North",
        latitude=37.8044,
        longitude=-122.2712,
        service_time_mins=45.0,
        incident_id="INC-101",
    )
    assert site.incident_id == "INC-101"
    assert site.service_time_mins == 45.0

    site_dict = site.to_dict()
    assert site_dict["id"] == "SITE-A"
    assert site_dict["service_time_mins"] == 45.0
    assert site_dict["incident_id"] == "INC-101"

    # Validation errors
    with pytest.raises(ValueError, match="non-empty string"):
        DispatchSite(id="", name="Invalid Site")

    with pytest.raises(ValueError, match="Latitude"):
        DispatchSite(id="INV-LAT", name="Bad Lat", latitude=95.0)

    with pytest.raises(ValueError, match="Longitude"):
        DispatchSite(id="INV-LON", name="Bad Lon", longitude=-195.0)

    with pytest.raises(ValueError, match="Service time"):
        DispatchSite(id="INV-SVC", name="Bad Service", service_time_mins=-10.0)


def test_reduced_matrix_reduction_and_bounds():
    """Verify row and column reductions produce valid zeros and admissible lower bounds."""
    # 4x4 matrix
    inf = math.inf
    matrix = [
        [inf, 10.0, 15.0, 20.0],
        [10.0, inf, 35.0, 25.0],
        [15.0, 35.0, inf, 30.0],
        [20.0, 25.0, 30.0, inf],
    ]

    reduced, reduction_cost = ReducedMatrix.reduce_matrix(matrix)
    assert reduction_cost > 0.0

    n = len(reduced)
    # Every row and column must contain at least one 0.0
    for i in range(n):
        row_zeros = [reduced[i][j] for j in range(n) if reduced[i][j] == 0.0]
        assert len(row_zeros) >= 1, f"Row {i} should have at least one zero"

    for j in range(n):
        col_zeros = [reduced[i][j] for i in range(n) if reduced[i][j] == 0.0]
        assert len(col_zeros) >= 1, f"Column {j} should have at least one zero"

    # Verify monotonicity in child matrix creation
    child_mat, child_lb = ReducedMatrix.create_child_matrix(
        reduced, reduction_cost, u=0, v=1, start_node=0, is_final_step=False
    )
    assert child_lb >= reduction_cost


def test_nearest_neighbor_and_two_opt_heuristics():
    """Verify greedy construction and 2-Opt local search refinement."""
    matrix = [
        [math.inf, 2.0, 9.0, 10.0],
        [1.0, math.inf, 6.0, 4.0],
        [15.0, 7.0, math.inf, 8.0],
        [6.0, 3.0, 12.0, math.inf],
    ]

    tour, cost = NearestNeighborHeuristic.construct_tour(matrix, start_idx=0)
    assert len(tour) == 5
    assert tour[0] == 0 and tour[-1] == 0
    assert set(tour) == {0, 1, 2, 3}
    assert cost > 0.0

    # 2-Opt optimization
    opt_tour, opt_cost = TwoOptLocalSearch.optimize(tour, matrix)
    assert len(opt_tour) == 5
    assert opt_tour[0] == 0 and opt_tour[-1] == 0
    assert opt_cost <= cost + 1e-6

    # Verify tour cost calculation helper
    calc_cost = TwoOptLocalSearch.calculate_tour_cost(opt_tour, matrix)
    assert math.isclose(opt_cost, calc_cost, rel_tol=1e-5)


def test_branch_and_bound_exact_optimality_against_brute_force():
    """Verify Branch-and-Bound discovers the provably optimal tour against exhaustive permutations."""
    # Test on multiple random distance matrices of sizes n=4, 5, 6
    random.seed(123)

    for n in [4, 5, 6]:
        for trial in range(3):
            cost_matrix = [[0.0] * n for _ in range(n)]
            for i in range(n):
                for j in range(n):
                    if i != j:
                        cost_matrix[i][j] = float(random.randint(10, 80))

            # Exhaustive Brute-Force baseline
            optimal_cost = math.inf
            optimal_tour = None
            for perm in itertools.permutations(range(1, n)):
                candidate = [0] + list(perm) + [0]
                cand_cost = TwoOptLocalSearch.calculate_tour_cost(candidate, cost_matrix)
                if cand_cost < optimal_cost:
                    optimal_cost = cand_cost
                    optimal_tour = candidate

            # Branch-and-Bound solver
            sites = [
                DispatchSite(id=f"S{i}", name=f"Site {i}", is_depot=(i == 0))
                for i in range(n)
            ]
            solver = BranchAndBoundTSPSolver()
            manifest = solver.solve(sites, cost_matrix)

            assert manifest.is_exact_optimal is True
            assert math.isclose(manifest.total_distance, optimal_cost, rel_tol=1e-5), (
                f"Mismatch for n={n}, trial={trial}: B&B={manifest.total_distance}, BF={optimal_cost}"
            )
            # Verify tour starts and finishes at depot
            assert manifest.site_sequence[0].id == "S0"
            assert manifest.site_sequence[-1].id == "S0"
            assert len(manifest.site_sequence) == n + 1


def test_branch_and_bound_edge_cases():
    """Verify trivial clusters (n=1, n=2) and small degenerate topologies."""
    # n = 1 (Depot only)
    depot = [DispatchSite(id="DEPOT", name="Main Depot", is_depot=True)]
    solver = BranchAndBoundTSPSolver()
    m1 = solver.solve(depot, [[0.0]])
    assert m1.total_distance == 0.0
    assert m1.is_exact_optimal is True
    assert len(m1.site_sequence) == 2

    # n = 2 (Depot + 1 site)
    sites = [
        DispatchSite(id="DEPOT", name="Main Depot", is_depot=True),
        DispatchSite(id="REMOTE", name="Remote Repeater", service_time_mins=25.0),
    ]
    matrix = [[0.0, 15.0], [15.0, 0.0]]
    m2 = solver.solve(sites, matrix)
    assert m2.total_distance == 30.0
    assert m2.total_service_time_mins == 25.0
    assert m2.total_mission_time_mins == 55.0
    assert [s.id for s in m2.site_sequence] == ["DEPOT", "REMOTE", "DEPOT"]


def test_adaptive_dispatch_engine_routing_integration():
    """Verify Floyd-Warshall distance integration and adaptive threshold switching."""
    graph = NetworkGraph()
    # Create 6 network hubs in a ring topology
    for i in range(6):
        graph.add_node(Node(id=f"HUB_{i}", name=f"Network Hub {i}", node_type=NodeType.NETWORK_HUB))

    graph.add_edge(NetworkEdge("HUB_0", "HUB_1", weight=10.0, latency_ms=10.0))
    graph.add_edge(NetworkEdge("HUB_1", "HUB_2", weight=12.0, latency_ms=12.0))
    graph.add_edge(NetworkEdge("HUB_2", "HUB_3", weight=15.0, latency_ms=15.0))
    graph.add_edge(NetworkEdge("HUB_3", "HUB_4", weight=11.0, latency_ms=11.0))
    graph.add_edge(NetworkEdge("HUB_4", "HUB_5", weight=14.0, latency_ms=14.0))
    graph.add_edge(NetworkEdge("HUB_5", "HUB_0", weight=13.0, latency_ms=13.0))

    engine = AdaptiveDispatchEngine(exact_threshold=4)

    # 1. Dispatch tour with 3 sites (<= threshold 4) -> should use exact B&B
    manifest_exact = engine.schedule_maintenance_tour(
        graph,
        depot_node_id="HUB_0",
        target_site_ids=["HUB_1", "HUB_2"],
    )
    assert manifest_exact.is_exact_optimal is True
    assert "Branch-and-Bound" in manifest_exact.solver_name
    assert manifest_exact.site_sequence[0].id == "HUB_0"
    assert manifest_exact.site_sequence[-1].id == "HUB_0"
    assert manifest_exact.total_distance > 0.0

    # 2. Dispatch tour with 5 sites (> threshold 4) -> should auto-switch to 2-Opt heuristic
    manifest_heur = engine.schedule_maintenance_tour(
        graph,
        depot_node_id="HUB_0",
        target_site_ids=["HUB_1", "HUB_2", "HUB_3", "HUB_4", "HUB_5"],
    )
    assert manifest_heur.is_exact_optimal is False
    assert "2-Opt" in manifest_heur.solver_name
    assert manifest_heur.optimality_gap_pct > 0.0
    assert len(manifest_heur.site_sequence) == 7  # Depot + 5 sites + Depot

    # 3. Forced solver override
    manifest_forced = engine.schedule_maintenance_tour(
        graph,
        depot_node_id="HUB_0",
        target_site_ids=["HUB_1", "HUB_2"],
        force_solver="heuristic",
    )
    assert manifest_forced.is_exact_optimal is False
    assert "2-Opt" in manifest_forced.solver_name


def test_backtracking_vs_branch_and_bound_comparison():
    """Verify Backtracking TSP matches Branch-and-Bound exact optimality while B&B explores fewer states."""
    random.seed(99)
    n = 7
    cost_matrix = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            if i != j:
                cost_matrix[i][j] = float(random.randint(12, 95))

    sites = [DispatchSite(id=f"S{i}", name=f"Site {i}", is_depot=(i == 0)) for i in range(n)]

    bt_solver = BacktrackingTSPSolver()
    bnb_solver = BranchAndBoundTSPSolver()

    res_bt = bt_solver.solve(sites, cost_matrix)
    res_bnb = bnb_solver.solve(sites, cost_matrix)

    assert res_bt.is_exact_optimal is True
    assert res_bnb.is_exact_optimal is True
    assert math.isclose(res_bt.total_distance, res_bnb.total_distance, rel_tol=1e-5)
    # Branch-and-Bound with Reduced Matrix LB + 2-Opt UB explores far fewer states than DFS Backtracking
    assert res_bnb.nodes_explored < res_bt.nodes_explored

