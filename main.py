"""Unified Assignment 4 Demonstration Pipeline & Interactive Viva Console.

Follows the prescribed DAA Framework Structure (Page 2 & Page 7 of Assignment Handout):
SCENARIO INPUT -> PROBLEM MODEL -> DAA CHOICE -> EXECUTION -> ANALYSIS -> EXPLANATION / ADAPTATION

Usage:
  python main.py                 # Runs full 6-module demo, then offers Interactive Mode
  python main.py --interactive   # Launches directly into the Interactive Viva Console
"""

from __future__ import annotations

import random
import sys
from pathlib import Path

# Ensure project root is on sys.path
project_root = str(Path(__file__).parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from algorithms.mst.selector import AdaptiveMSTSelector
from algorithms.routing.floyd_warshall import FloydWarshallRouter
from budgeting.item import AssetCategory, UpgradeItem
from budgeting.selector import AdaptiveBudgetAllocator
from core.edge import NetworkEdge
from core.graph import NetworkGraph
from core.node import Node, NodeType
from dispatch.selector import AdaptiveDispatchEngine
from indexing.base import TelemetryRecord, WorkloadType
from indexing.selector import AdaptiveIndexSelector
from prioritization.binomial_heap import BinomialHeap
from prioritization.fibonacci_heap import FibonacciHeap
from prioritization.incident import IncidentSeverity, IncidentType, NetworkIncident
from prioritization.selector import AdaptiveTriageSelector


def build_synthetic_network(num_nodes: int, target_density: float, seed: int = 42) -> NetworkGraph:
    """Construct a connected weighted network graph with a target edge density."""
    rng = random.Random(seed)
    graph = NetworkGraph()

    for i in range(num_nodes):
        ntype = (
            NodeType.DATA_CENTER
            if i == 0
            else (NodeType.NETWORK_HUB if i < num_nodes // 2 else NodeType.IOT_GATEWAY)
        )
        graph.add_node(Node(id=f"N{i:02d}", name=f"{ntype.value}_{i:02d}", node_type=ntype))

    # 1. Spanning chain to guarantee connectivity
    for i in range(num_nodes - 1):
        w = round(rng.uniform(5.0, 40.0), 1)
        graph.add_edge(NetworkEdge(f"N{i:02d}", f"N{i+1:02d}", weight=w, latency_ms=w))

    # 2. Add random edges until target density is reached
    max_edges = (num_nodes * (num_nodes - 1)) // 2
    desired_edges = max(num_nodes - 1, int(target_density * max_edges))

    all_pairs = [
        (i, j) for i in range(num_nodes) for j in range(i + 2, num_nodes)
    ]
    rng.shuffle(all_pairs)

    for i, j in all_pairs:
        if graph.num_edges >= desired_edges:
            break
        w = round(rng.uniform(8.0, 75.0), 1)
        graph.add_edge(NetworkEdge(f"N{i:02d}", f"N{j:02d}", weight=w, latency_ms=w))

    return graph


def print_banner(title: str) -> None:
    print("\n" + "=" * 105)
    print(f" {title}")
    print("=" * 105)


# ==============================================================================
# AUTOMATED 6-MODULE PIPELINE FUNCTIONS
# ==============================================================================

def demo_module_1_mst() -> NetworkGraph:
    print_banner("MODULE 1: MINIMUM-COST BACKBONE (PRIM'S VS. KRUSKAL'S ALGORITHM)")

    mst_selector = AdaptiveMSTSelector(density_threshold=0.35, dense_node_threshold=20)

    # Scenario 1A: Sparse Regional Topology
    sparse_graph = build_synthetic_network(num_nodes=25, target_density=0.12, seed=101)
    _, rationale_sparse = mst_selector.select_algorithm(sparse_graph)
    res_sparse = mst_selector.solve(sparse_graph)

    print("[1] SCENARIO INPUT : Regional Network with |V| = 25 hubs/gateways, |E| = "
          f"{sparse_graph.num_edges} links (Density D = {sparse_graph.density():.4f})")
    print("[2] PROBLEM MODEL  : Entities = Hubs/Links | Constraint = Acyclic Spanning Tree (|V|-1 edges) "
          "| Objective = Min Sum(w_e)")
    print(f"[3] DAA CHOICE     : {res_sparse.algorithm_name}")
    print(f"    Rationale      : {rationale_sparse}")
    print(f"[4] EXECUTION      : MST Total Cost = {res_sparse.total_weight:.2f} | "
          f"Backbone Edges = {len(res_sparse.edges)} | Spanning Tree = {res_sparse.is_spanning_tree}")
    print(f"[5] ANALYSIS       : Time = O(|E| log |E|) | Space = O(|V| + |E|) | "
          f"Runtime = {res_sparse.execution_time_ms:.3f} ms | Ops = {res_sparse.operations_count}")

    # Scenario 1B: Adaptation to Dense Metro Core
    dense_graph = build_synthetic_network(num_nodes=25, target_density=0.80, seed=202)
    _, rationale_dense = mst_selector.select_algorithm(dense_graph)
    res_dense = mst_selector.solve(dense_graph)

    print("\n[6] EXPLANATION / ADAPTATION (When Graph Density Changes):")
    print(f"    -> Scenario shifts to Dense Metro Mesh: |V| = 25, |E| = {dense_graph.num_edges} "
          f"(Density D = {dense_graph.density():.4f} >= 0.35).")
    print(f"    -> Framework Automatically Adapts To : {res_dense.algorithm_name}")
    print(f"    -> Rationale                         : {rationale_dense}")
    print(f"    -> Dense MST Total Cost = {res_dense.total_weight:.2f} | Runtime = {res_dense.execution_time_ms:.3f} ms | "
          f"Ops = {res_dense.operations_count}")

    return sparse_graph


def demo_module_2_all_pairs_routing(base_graph: NetworkGraph) -> None:
    print_banner("MODULE 2: ALL-PAIRS COST ANALYSIS (FLOYD-WARSHALL DYNAMIC PROGRAMMING)")

    router = FloydWarshallRouter(metric="latency_ms")

    print("[1] SCENARIO INPUT : Pairwise communication latency across |V| = 10, 20, 30 network zones.")
    print("[2] PROBLEM MODEL  : All-Pairs Shortest Path Matrix D[i][j] | "
          "DP Recurrence: D^(k)[i][j] = min(D^(k-1)[i][j], D^(k-1)[i][k] + D^(k-1)[k][j])")
    print("[3] DAA CHOICE     : Floyd-Warshall Algorithm (Dynamic Programming)")

    print("[4] EXECUTION & [5] SCALING ANALYSIS AS |V| INCREASES:")
    print(f"    {'Zones |V|':<12} | {'Cubic Comparisons (|V|^3)':<26} | {'Relaxations':<14} | {'Runtime (ms)':<14} | {'Network Diameter':<18}")
    print("    " + "-" * 94)

    for v_count in [10, 20, 30]:
        g = build_synthetic_network(num_nodes=v_count, target_density=0.25, seed=300 + v_count)
        res = router.compute_routing(g)
        print(f"    {v_count:<12} | {res.comparisons_count:<26} | {res.relaxations_count:<14} | "
              f"{res.execution_time_ms:<14.3f} | {res.network_diameter():<18.2f}")

    res_base = router.compute_routing(base_graph)
    path_idx = res_base.reconstruct_path_indices(0, 24)
    path_ids = [res_base.node_ids[idx] for idx in path_idx]
    dist_sample = res_base.get_distance("N00", "N24")
    print(f"\n[6] EXPLANATION    : Sample Optimal Route N00 -> N24: {' -> '.join(path_ids)} (Latency: {dist_sample:.1f} ms)")
    print("    -> Complexity is strictly Theta(|V|^3) time and Theta(|V|^2) space.")
    print("    -> Increasing |V| from 10 -> 20 -> 30 increases comparisons from 1,000 -> 8,000 -> 27,000 (exact cubic scaling).")


def demo_module_3_indexing() -> None:
    print_banner("MODULE 3: NETWORK-STATE DATA MANAGEMENT (RED-BLACK TREE VS. ORDER-t B-TREE)")

    selector = AdaptiveIndexSelector(btree_order=16)

    print("[1] SCENARIO INPUT : 1,000 searchable network telemetry records & historical state logs.")
    print("[2] PROBLEM MODEL  : Ordered Key-Value Index supporting O(log N) search, insertion, and range queries.")

    # Scenario 3A: In-Memory Real-Time Telemetry (Red-Black Tree)
    for k in range(1, 501):
        rec = TelemetryRecord(
            node_id=f"N{k % 25:02d}",
            metric_name="cpu_load_pct",
            value=45.0 + (k % 50),
            timestamp_ns=1700000000000 + k,
        )
        selector.store_telemetry(rec, workload=WorkloadType.VOLATILE_TELEMETRY)

    stats_after_ram = selector.get_tier_statistics()
    print("[3] DAA CHOICE (A) : Red-Black Tree (In-Memory Volatile L1 Index)")
    print("    Justification  : Real-time telemetry stream requires O(log2 N) lookup with <= 2 rotations per insert.")
    print(f"[4] EXECUTION (A)  : Inserted {stats_after_ram['rbt_in_memory_records']} records | "
          f"Rotations = {stats_after_ram['rbt_rotations_total']} | Recolorings = {stats_after_ram['rbt_recolorings_total']}")
    print("[5] ANALYSIS (A)   : Time = O(log2 N) search/insert, Space = O(N) | Zero disk I/O latency.")

    # Scenario 3B: Adaptation to Disk-Backed Historical Archive (B-Tree)
    for k in range(501, 1001):
        rec = TelemetryRecord(
            node_id=f"N{k % 25:02d}",
            metric_name="historical_audit",
            value=float(k),
            timestamp_ns=1700000000000 + k,
        )
        selector.store_telemetry(rec, workload=WorkloadType.HISTORICAL_LOGS)

    stats_final = selector.get_tier_statistics()
    print("\n[6] EXPLANATION / ADAPTATION (When Workload Shifts to Persistent Disk Archive):")
    print("    -> Framework Automatically Routes To : Order-t B-Tree (Disk-Backed Block Storage, t=16)")
    print("    -> Justification                     : High branching factor packs up to 31 keys per block,")
    print("                                           reducing tree height to O(log_t N) to minimize disk I/O seeks.")
    print(f"    -> Execution Telemetry               : Stored {stats_final['btree_persistent_records']} records | "
          f"Node Splits = {stats_final['btree_splits_total']} | Simulated Block Writes = {stats_final['btree_disk_writes_total']}")


def demo_module_4_prioritization() -> None:
    print_banner("MODULE 4: EVENT PRIORITIZATION (BINOMIAL HEAP VS. FIBONACCI HEAP)")

    triage_selector = AdaptiveTriageSelector(escalation_threshold=0.20, initial_queue_type="binomial")

    print("[1] SCENARIO INPUT : Fault & maintenance alarms across network hubs with dynamic priority escalations.")
    print("[2] PROBLEM MODEL  : Mergeable Min-Priority Queue supporting insert, extract_min, union, and decrease_key.")

    # Scenario 4A: Steady-State Fault Queue (Low Escalations)
    for i in range(1, 51):
        inc = NetworkIncident(
            id=f"INC-{i:03d}",
            node_id=f"N{i % 25:02d}",
            incident_type=IncidentType.CONGESTION,
            severity=IncidentSeverity.MEDIUM,
            priority_score=float(100 + i),
            description="Routine link packet loss",
        )
        triage_selector.ingest_incident(inc)

    triage_selector.escalate_incident("INC-025", score_reduction=95.0)
    triage_selector.escalate_incident("INC-010", score_reduction=80.0)
    metrics_steady = triage_selector.get_triage_metrics()
    top_steady = triage_selector.peek_highest_priority()

    print(f"[3] DAA CHOICE (A) : {metrics_steady['selected_algorithm']}")
    print(f"    Justification  : Steady-state workload (Escalation Ratio = {metrics_steady['escalation_ratio']:.3f} < 0.20) "
          "favors deterministic O(log N) Binomial Heap.")
    print(f"[4] EXECUTION (A)  : Active Alarms = {metrics_steady['active_incidents']} | "
          f"Top Priority Alarm = {top_steady.id} (Score = {top_steady.priority_score:.1f})")
    print(f"[5] ANALYSIS (A)   : Insert/Decrease-Key/Extract-Min = O(log N) | Comparisons = {metrics_steady['raw_queue_telemetry']['comparisons']}")

    # Scenario 4B: Adaptation to Cascading Outage Storm (High decrease_key frequency)
    for i in range(11, 35):
        triage_selector.escalate_incident(f"INC-{i:03d}", score_reduction=50.0)

    metrics_storm = triage_selector.get_triage_metrics()
    dispatched = triage_selector.dispatch_highest_priority()

    print("\n[6] EXPLANATION / ADAPTATION (When Cascading Failure Storm Hits):")
    print(f"    -> Escalation Ratio surged to {metrics_storm['escalation_ratio']:.3f} (>= {metrics_storm['escalation_threshold']} threshold).")
    print(f"    -> Framework Automatically Migrates Live Queue To : {metrics_storm['selected_algorithm']}")
    print("    -> Justification : Fibonacci Heap executes decrease_key and union in O(1) amortized time via cascading cuts!")
    print(f"    -> Dispatched    : {dispatched.id} on {dispatched.node_id} (Final Score = {dispatched.priority_score:.1f})")


def demo_module_5_budgeting() -> None:
    print_banner("MODULE 5: UPGRADE BUDGETING (FRACTIONAL KNAPSACK GREEDY VS. 0/1 KNAPSACK DP)")

    allocator = AdaptiveBudgetAllocator(precision_scale=1)

    divisible_proposals = [
        UpgradeItem("BW-01", "100G Optical Wavelength Lease", AssetCategory.BANDWIDTH_TRANSIT, cost=40.0, utility_value=240.0, is_divisible=True),
        UpgradeItem("BW-02", "Metro Dark Fiber Spectrum", AssetCategory.BANDWIDTH_TRANSIT, cost=60.0, utility_value=300.0, is_divisible=True),
        UpgradeItem("BW-03", "Cloud Peering Burst Pipe", AssetCategory.BANDWIDTH_TRANSIT, cost=50.0, utility_value=200.0, is_divisible=True),
    ]

    indivisible_proposals = [
        UpgradeItem("HW-01", "Core Terabit Chassis Router", AssetCategory.CORE_CHASSIS, cost=50.0, utility_value=160.0, is_divisible=False),
        UpgradeItem("HW-02", "Edge Compute Server Rack", AssetCategory.SERVER_RACK, cost=30.0, utility_value=120.0, is_divisible=False),
        UpgradeItem("HW-03", "Redundant Battery Backup Unit", AssetCategory.BATTERY_BACKUP, cost=40.0, utility_value=150.0, is_divisible=False),
        UpgradeItem("HW-04", "400G Optical Transceiver Pack", AssetCategory.OPTICAL_TRANSCEIVER, cost=20.0, utility_value=90.0, is_divisible=False),
    ]

    print("[1] SCENARIO INPUT : Capital Budget W = $100.0k across Divisible Bandwidth vs. Indivisible Hardware.")
    print("[2] PROBLEM MODEL  : Maximize Sum(v_i * x_i) subject to Sum(w_i * x_i) <= W.")

    # Scenario 5A: Divisible Bandwidth (Fractional Knapsack)
    res_frac = allocator.allocate(divisible_proposals, budget=100.0)
    print(f"[3] DAA CHOICE (A) : {res_frac.solver_name} (Automatically selected because all items are divisible: x_i in [0, 1])")
    print(f"[4] EXECUTION (A)  : Total Utility = {res_frac.total_value:.1f} | Spent = ${res_frac.total_cost:.1f}k "
          f"({res_frac.budget_utilization * 100:.1f}% utilization)")
    for s in res_frac.slices:
        print(f"                     - {s.item.id} ({s.item.name}): {s.fraction * 100:.1f}% funded (${s.allocated_cost:.1f}k)")
    print("[5] ANALYSIS (A)   : Strictly Polynomial Time O(N log N) via greedy value-density sorting (v_i / w_i).")

    # Scenario 5B: Indivisible Hardware (0/1 Knapsack DP)
    res_disc = allocator.allocate(indivisible_proposals, budget=100.0)
    print("\n[6] EXPLANATION / ADAPTATION (When Proposals Are Indivisible Hardware Units):")
    print(f"    -> Framework Automatically Switches To : {res_disc.solver_name} (Discrete x_i in {{0, 1}})")
    print(f"    -> Execution          : Total Utility = {res_disc.total_value:.1f} | Spent = ${res_disc.total_cost:.1f}k "
          f"| DP Table States Evaluated = {res_disc.operations_count}")
    for s in res_disc.slices:
        print(f"                            - {s.item.id} ({s.item.name}): 100% unit purchased (${s.allocated_cost:.1f}k)")
    print("    -> Complexity Precision : 0/1 Knapsack DP runs in O(N * W) PSEUDO-POLYNOMIAL time (exponential in input bit-length log2(W)),")
    print("                              whereas the 0/1 Knapsack Decision Problem is NP-COMPLETE.")


def demo_module_6_and_7_tsp_and_complexity(base_graph: NetworkGraph) -> None:
    print_banner("MODULES 6 & 7: MAINTENANCE TOUR (TSP) & NP-HARD COMPLEXITY LIMITS")

    engine = AdaptiveDispatchEngine(exact_threshold=14)
    target_sites_small = ["N03", "N07", "N11", "N15", "N18", "N21", "N24"]  # Depot N00 + 7 sites = 8 vertices

    print("[1] SCENARIO INPUT : Field Engineer at Depot N00 must visit 7 damaged sites (8 total vertices) and return.")
    print("[2] PROBLEM MODEL  : Complete Weighted Graph G=(V,E) from Floyd-Warshall latencies | "
          "Find minimum-cost Hamiltonian cycle.")
    print("[3] DAA COMPARISON : Exact DFS Backtracking vs. Exact Branch-and-Bound (Reduced Cost Matrix Lower Bound)")

    manifest_bt = engine.schedule_maintenance_tour(
        base_graph, depot_node_id="N00", target_site_ids=target_sites_small, force_solver="backtracking"
    )
    manifest_bnb = engine.schedule_maintenance_tour(
        base_graph, depot_node_id="N00", target_site_ids=target_sites_small, force_solver="branch_and_bound"
    )

    print("\n[4] EXECUTION & [5] STATE-SPACE PRUNING COMPARISON (|V| = 8 Sites):")
    print(f"    {'Syllabus Method':<64} | {'Optimal Cost':<13} | {'States Explored':<16} | {'States Pruned':<14} | {'Time (ms)':<10}")
    print("    " + "-" * 124)
    print(f"    {manifest_bt.solver_name:<64} | {manifest_bt.total_distance:<13.2f} | "
          f"{manifest_bt.nodes_explored:<16} | {manifest_bt.nodes_pruned:<14} | {manifest_bt.execution_time_ms:<10.2f}")
    print(f"    {manifest_bnb.solver_name:<64} | {manifest_bnb.total_distance:<13.2f} | "
          f"{manifest_bnb.nodes_explored:<16} | {manifest_bnb.nodes_pruned:<14} | {manifest_bnb.execution_time_ms:<10.2f}")

    print(f"\n    Optimal Maintenance Tour : {' -> '.join(manifest_bnb.tour_node_ids())}")
    print(f"    Total Transit Cost       : {manifest_bnb.total_distance:.2f} ms | "
          f"On-Site Service Time: {manifest_bnb.total_service_time_mins:.1f} mins")

    # Scenario 6B: Large-Scale NP-Hard Cutoff Demonstration (22 sites)
    all_target_sites = [f"N{i:02d}" for i in range(1, 22)]
    manifest_large = engine.schedule_maintenance_tour(
        base_graph, depot_node_id="N00", target_site_ids=all_target_sites
    )

    print("\n[6] COMPLEXITY AWARENESS & SCALABILITY ADAPTATION (NP-Hard vs. NP-Complete):")
    print("    -> Formal Distinction : Optimization TSP ('Find minimum-cost tour') is NP-HARD.")
    print("                            Decision TSP ('Does a tour with cost <= K exist?') is NP-COMPLETE.")
    print("    -> Scalability Limit  : Exact search grows as O((|V|-1)!). For |V| = 22 sites, 21! = 5.1 x 10^19 permutations.")
    print(f"    -> Framework Behavior : When cluster size reaches |V| = {len(all_target_sites) + 1} (> exact cutoff 14),")
    print(f"                            framework adapts to: {manifest_large.solver_name}")
    print(f"                            completing in {manifest_large.execution_time_ms:.2f} ms with total distance {manifest_large.total_distance:.2f}.")


# ==============================================================================
# INTERACTIVE VIVA CONSOLE FUNCTIONS
# ==============================================================================

def _prompt_int(prompt_text: str, default: int, min_val: int, max_val: int) -> int:
    raw = input(f"  {prompt_text} [default={default}, range={min_val}..{max_val}]: ").strip()
    if not raw:
        return default
    try:
        val = int(raw)
        return max(min_val, min(max_val, val))
    except ValueError:
        print(f"  -> Invalid integer, using default {default}.")
        return default


def _prompt_float(prompt_text: str, default: float, min_val: float, max_val: float) -> float:
    raw = input(f"  {prompt_text} [default={default}, range={min_val}..{max_val}]: ").strip()
    if not raw:
        return default
    try:
        val = float(raw)
        return max(min_val, min(max_val, val))
    except ValueError:
        print(f"  -> Invalid number, using default {default}.")
        return default


def interactive_mst() -> None:
    print_banner("INTERACTIVE MODULE 1: MINIMUM-COST BACKBONE (KRUSKAL VS. PRIM)")
    v = _prompt_int("Enter number of network hubs |V|", default=30, min_val=4, max_val=200)
    d = _prompt_float("Enter target edge density D (try 0.15 for Sparse or 0.80 for Dense)", default=0.15, min_val=0.05, max_val=1.0)

    graph = build_synthetic_network(num_nodes=v, target_density=d, seed=42)
    selector = AdaptiveMSTSelector(density_threshold=0.35, dense_node_threshold=20)
    _, rationale = selector.select_algorithm(graph)
    chosen_res = selector.solve(graph)

    # Also run both Kruskal and Prim side by side to prove why the choice won
    res_kruskal = selector.solve(graph, force_algorithm="kruskal")
    res_prim_heap = selector.solve(graph, force_algorithm="prim_heap")
    res_prim_dense = selector.solve(graph, force_algorithm="prim_dense")

    print(f"\n[1] SCENARIO INPUT : |V| = {graph.num_nodes} nodes, |E| = {graph.num_edges} links, Actual Density D = {graph.density():.4f}")
    print("[2] PROBLEM MODEL  : Minimum Spanning Tree (Acyclic connected subgraph with |V|-1 edges)")
    print(f"[3] DAA CHOICE     : {chosen_res.algorithm_name}")
    print(f"    Rationale      : {rationale}")
    print("\n[4] EXECUTION & [5] SIDE-BY-SIDE SYLLABUS COMPARISON:")
    print(f"    {'Algorithm':<52} | {'MST Cost':<12} | {'Runtime (ms)':<14} | {'Operations':<12}")
    print("    " + "-" * 98)
    for r in (res_kruskal, res_prim_heap, res_prim_dense):
        marker = " <-- SELECTED" if r.algorithm_name == chosen_res.algorithm_name else ""
        print(f"    {r.algorithm_name:<52} | {r.total_weight:<12.2f} | {r.execution_time_ms:<14.3f} | {r.operations_count:<12}{marker}")


def interactive_floyd_warshall() -> None:
    print_banner("INTERACTIVE MODULE 2: ALL-PAIRS ROUTING (FLOYD-WARSHALL)")
    v = _prompt_int("Enter number of network zones |V|", default=20, min_val=3, max_val=100)
    d = _prompt_float("Enter network connectivity density D", default=0.25, min_val=0.05, max_val=1.0)

    graph = build_synthetic_network(num_nodes=v, target_density=d, seed=99)
    router = FloydWarshallRouter(metric="latency_ms")
    res = router.compute_routing(graph)

    src_id = "N00"
    dst_id = f"N{v-1:02d}"
    path_idx = res.reconstruct_path_indices(0, v - 1)
    path_str = " -> ".join(res.node_ids[idx] for idx in path_idx)

    print(f"\n[1] SCENARIO INPUT : |V| = {v} zones, |E| = {graph.num_edges} links")
    print("[2] PROBLEM MODEL  : All-Pairs Shortest Path DP: D^(k)[i][j] = min(D^(k-1)[i][j], D^(k-1)[i][k] + D^(k-1)[k][j])")
    print("[3] DAA CHOICE     : Floyd-Warshall Algorithm (Dynamic Programming)")
    print(f"[4] EXECUTION      : Optimal Route {src_id} -> {dst_id}: {path_str} (Cost = {res.get_distance(src_id, dst_id):.2f} ms)")
    print(f"[5] ANALYSIS       : Exact Cubic Comparisons = {res.comparisons_count} (|V|^3 = {v**3}) | "
          f"Successful Relaxations = {res.relaxations_count} | Runtime = {res.execution_time_ms:.3f} ms")
    print(f"[6] EXPLANATION    : Network Diameter = {res.network_diameter():.2f} ms | Reachability = {res.reachability_ratio()*100:.1f}%")


def interactive_indexing() -> None:
    print_banner("INTERACTIVE MODULE 3: NETWORK-STATE DATA MANAGEMENT (RED-BLACK TREE VS. B-TREE)")
    print("  Select Storage Workload Profile:")
    print("    1 = Real-Time Volatile RAM Telemetry (High-speed inserts & lookups)")
    print("    2 = Persistent Disk Block Archive (Historical audit logs)")
    mode = _prompt_int("Choose workload type (1 or 2)", default=1, min_val=1, max_val=2)
    count = _prompt_int("Enter number of telemetry records to index", default=1000, min_val=10, max_val=10000)
    btree_t = _prompt_int("Enter B-Tree minimum degree t (block branching factor)", default=16, min_val=2, max_val=64)

    selector = AdaptiveIndexSelector(btree_order=btree_t)
    workload = WorkloadType.VOLATILE_TELEMETRY if mode == 1 else WorkloadType.HISTORICAL_LOGS

    # Run both to compare metrics on the exact same record count
    for k in range(1, count + 1):
        rec = TelemetryRecord(node_id=f"N{k % 25:02d}", metric_name="telemetry", value=float(k), timestamp_ns=1700000000000 + k)
        selector.store_telemetry(rec, workload=WorkloadType.VOLATILE_TELEMETRY)
        selector.store_telemetry(rec, workload=WorkloadType.HISTORICAL_LOGS)

    stats = selector.get_tier_statistics()
    chosen_name = "Red-Black Tree (In-Memory RAM)" if workload == WorkloadType.VOLATILE_TELEMETRY else f"Order-t B-Tree (Disk Block, t={btree_t})"

    print(f"\n[1] SCENARIO INPUT : {count} telemetry records | Mode = {workload.value}")
    print("[2] PROBLEM MODEL  : Balanced Search Tree Index supporting O(log N) search, insert, and ordered range scans.")
    print(f"[3] DAA CHOICE     : {chosen_name}")
    print("\n[4] EXECUTION & [5] SIDE-BY-SIDE DATA STRUCTURE COMPARISON:")
    print(f"    - Red-Black Tree (RAM)  : Records = {stats['rbt_in_memory_records']} | "
          f"Rotations = {stats['rbt_rotations_total']} (<= 2/insert) | Recolorings = {stats['rbt_recolorings_total']} | Disk I/O = 0")
    print(f"    - Order-{btree_t} B-Tree (Disk) : Records = {stats['btree_persistent_records']} | "
          f"Node Splits = {stats['btree_splits_total']} | Simulated Disk Block Writes = {stats['btree_disk_writes_total']}")


def interactive_prioritization() -> None:
    print_banner("INTERACTIVE MODULE 4: EVENT PRIORITIZATION (BINOMIAL HEAP VS. FIBONACCI HEAP)")
    inc_count = _prompt_int("Enter number of active fault alarms to ingest", default=100, min_val=10, max_val=5000)
    esc_count = _prompt_int("Enter number of decrease_key priority escalations (try 5 for Steady or 60 for Storm)", default=60, min_val=0, max_val=inc_count)

    selector = AdaptiveTriageSelector(escalation_threshold=0.20, initial_queue_type="binomial")
    for i in range(1, inc_count + 1):
        selector.ingest_incident(
            NetworkIncident(
                id=f"INC-{i:04d}",
                node_id=f"N{i % 25:02d}",
                incident_type=IncidentType.LINK_FAILURE,
                severity=IncidentSeverity.HIGH,
                priority_score=float(200 + i),
            )
        )

    for i in range(1, esc_count + 1):
        selector.escalate_incident(f"INC-{i:04d}", score_reduction=150.0)

    metrics = selector.get_triage_metrics()
    top_inc = selector.dispatch_highest_priority()

    print(f"\n[1] SCENARIO INPUT : {inc_count} alarms ingested, {esc_count} priority escalations "
          f"(Escalation Ratio = {metrics['escalation_ratio']:.3f})")
    print("[2] PROBLEM MODEL  : Mergeable Priority Queue supporting insert, extract_min, union, and decrease_key.")
    print(f"[3] DAA CHOICE     : {metrics['selected_algorithm']}")
    if metrics["escalation_ratio"] >= 0.20:
        print("    Rationale      : Escalation Ratio >= 0.20 threshold -> Live-migrated to Fibonacci Heap for O(1) amortized decrease_key!")
    else:
        print("    Rationale      : Escalation Ratio < 0.20 threshold -> Retained Binomial Heap for deterministic O(log N) performance.")
    print(f"[4] EXECUTION      : Most Critical Dispatched Incident = {top_inc.id} (Final Priority Score = {top_inc.priority_score:.1f})")
    print(f"[5] ANALYSIS       : Queue Comparisons = {metrics['raw_queue_telemetry']['comparisons']} | "
          f"Decrease-Keys = {metrics['raw_queue_telemetry']['decrease_keys']}")


def interactive_budgeting() -> None:
    print_banner("INTERACTIVE MODULE 5: UPGRADE BUDGETING (FRACTIONAL GREEDY VS. 0/1 KNAPSACK DP)")
    print("  Select Upgrade Portfolio Type:")
    print("    1 = Divisible Bandwidth Leases Only   -> Selects Fractional Knapsack (Greedy O(N log N))")
    print("    2 = Indivisible Router Hardware Only  -> Selects 0/1 Knapsack (Dynamic Programming O(N * W))")
    print("    3 = Mixed Hybrid Portfolio            -> Partitions Discrete DP + Residual Fractional Greedy")
    mode = _prompt_int("Choose portfolio mode (1, 2, or 3)", default=2, min_val=1, max_val=3)
    budget = _prompt_float("Enter total capital budget W ($k)", default=100.0, min_val=10.0, max_val=500.0)

    divisible_items = [
        UpgradeItem("BW-01", "100G Wavelength Lease", AssetCategory.BANDWIDTH_TRANSIT, cost=40.0, utility_value=240.0, is_divisible=True),
        UpgradeItem("BW-02", "Dark Fiber Spectrum", AssetCategory.BANDWIDTH_TRANSIT, cost=60.0, utility_value=300.0, is_divisible=True),
        UpgradeItem("BW-03", "Cloud Peering Pipe", AssetCategory.BANDWIDTH_TRANSIT, cost=50.0, utility_value=200.0, is_divisible=True),
    ]
    discrete_items = [
        UpgradeItem("HW-01", "Core Terabit Chassis", AssetCategory.CORE_CHASSIS, cost=50.0, utility_value=160.0, is_divisible=False),
        UpgradeItem("HW-02", "Edge Compute Rack", AssetCategory.SERVER_RACK, cost=30.0, utility_value=120.0, is_divisible=False),
        UpgradeItem("HW-03", "Battery Backup Unit", AssetCategory.BATTERY_BACKUP, cost=40.0, utility_value=150.0, is_divisible=False),
        UpgradeItem("HW-04", "400G Optical Pack", AssetCategory.OPTICAL_TRANSCEIVER, cost=20.0, utility_value=90.0, is_divisible=False),
    ]

    items = divisible_items if mode == 1 else (discrete_items if mode == 2 else discrete_items + divisible_items)
    allocator = AdaptiveBudgetAllocator(precision_scale=1)
    res = allocator.allocate(items, budget=budget)

    print(f"\n[1] SCENARIO INPUT : {len(items)} upgrade proposals | Budget W = ${budget:.1f}k")
    print("[2] PROBLEM MODEL  : Maximize Sum(v_i * x_i) subject to Sum(w_i * x_i) <= W")
    print(f"[3] DAA CHOICE     : {res.solver_name}")
    print(f"[4] EXECUTION      : Total Utility Achieved = {res.total_value:.2f} | Budget Spent = ${res.total_cost:.2f}k "
          f"({res.budget_utilization*100:.1f}%)")
    for s in res.slices:
        print(f"                     - {s.item.id} ({s.item.name}): {s.fraction*100:.1f}% funded (${s.allocated_cost:.1f}k -> Utility +{s.achieved_value:.1f})")
    print(f"[5] ANALYSIS       : Operations / DP States = {res.operations_count} | Runtime = {res.execution_time_ms:.3f} ms")
    print("[6] COMPLEXITY     : Fractional Knapsack is O(N log N) Polynomial; 0/1 Knapsack DP is O(N * W) Pseudo-Polynomial (Decision form is NP-Complete).")


def interactive_tsp() -> None:
    print_banner("INTERACTIVE MODULES 6 & 7: MAINTENANCE TOUR (TSP) & NP-HARD SCALABILITY")
    n_sites = _prompt_int(
        "Enter total number of sites N (try 6..10 to compare Backtracking vs B&B, or 20 for NP-Hard cutoff)",
        default=8,
        min_val=3,
        max_val=40,
    )

    graph = build_synthetic_network(num_nodes=max(25, n_sites + 2), target_density=0.30, seed=77)
    engine = AdaptiveDispatchEngine(exact_threshold=14)
    targets = [f"N{i:02d}" for i in range(1, n_sites)]

    print(f"\n[1] SCENARIO INPUT : Depot N00 + {len(targets)} maintenance sites (Total N = {n_sites} vertices)")
    print("[2] PROBLEM MODEL  : Traveling Salesperson Problem (TSP) over Floyd-Warshall all-pairs latency matrix.")

    if n_sites <= 11:
        print(f"[3] DAA CHOICE     : Exact Search Regime (N = {n_sites} <= 14). Running BOTH Syllabus Exact Methods:")
        res_bt = engine.schedule_maintenance_tour(graph, "N00", targets, force_solver="backtracking")
        res_bnb = engine.schedule_maintenance_tour(graph, "N00", targets, force_solver="branch_and_bound")

        print("\n[4] EXECUTION & [5] STATE-SPACE PRUNING COMPARISON:")
        print(f"    {'Syllabus Method':<64} | {'Optimal Cost':<13} | {'States Explored':<16} | {'States Pruned':<14} | {'Time (ms)':<10}")
        print("    " + "-" * 124)
        print(f"    {res_bt.solver_name:<64} | {res_bt.total_distance:<13.2f} | "
              f"{res_bt.nodes_explored:<16} | {res_bt.nodes_pruned:<14} | {res_bt.execution_time_ms:<10.2f}")
        print(f"    {res_bnb.solver_name:<64} | {res_bnb.total_distance:<13.2f} | "
              f"{res_bnb.nodes_explored:<16} | {res_bnb.nodes_pruned:<14} | {res_bnb.execution_time_ms:<10.2f}")
        print(f"\n    Optimal Tour Sequence : {' -> '.join(res_bnb.tour_node_ids())}")
    else:
        res_auto = engine.schedule_maintenance_tour(graph, "N00", targets)
        print(f"[3] DAA CHOICE     : {res_auto.solver_name}")
        print(f"[4] EXECUTION      : Total Tour Distance = {res_auto.total_distance:.2f} ms | "
              f"States Explored = {res_auto.nodes_explored} | Runtime = {res_auto.execution_time_ms:.2f} ms")
        print(f"    Tour Sequence  : {' -> '.join(res_auto.tour_node_ids())}")

    print("\n[6] COMPLEXITY     : Optimization TSP is NP-Hard; Decision TSP is NP-Complete. "
          f"Exact permutation space for N={n_sites} is ({n_sites}-1)! = {1 if n_sites <= 1 else __import__('math').factorial(n_sites - 1):,}.")


def run_interactive_console() -> None:
    """Interactive menu loop for live Viva evaluation."""
    while True:
        print("\n" + "#" * 105)
        print("  INTERACTIVE VIVA CONSOLE -- ADAPTIVE NETWORK DESIGN & OPTIMIZATION FRAMEWORK (ASSIGNMENT 4)")
        print("#" * 105)
        print("  [1] Module 1: Minimum-Cost Backbone (MST)     -> Test Custom |V| & Density D (Kruskal vs. Prim)")
        print("  [2] Module 2: All-Pairs Cost Analysis         -> Test Custom Zone Count |V| (Floyd-Warshall)")
        print("  [3] Module 3: Network-State Data Indexing     -> Test RAM vs. Disk Block & Record Count (RBT vs. B-Tree)")
        print("  [4] Module 4: Fault Event Prioritization      -> Test Alarm Storm Escalations (Binomial vs. Fibonacci Heap)")
        print("  [5] Module 5: Upgrade Budget Allocation       -> Test Divisible/Discrete/Hybrid & Custom Budget W")
        print("  [6] Modules 6 & 7: Maintenance Tour (TSP)     -> Test Site Count N (Backtracking vs. B&B & NP-Hard Cutoff)")
        print("  [7] Run Complete 6-Module Automated Pipeline")
        print("  [0] Exit Interactive Console")
        print("-" * 105)

        try:
            choice = input("  Select an option [0-7]: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n  Exiting Interactive Console.")
            break

        if choice == "0" or choice.lower() in ("q", "quit", "exit"):
            print("  Exiting Interactive Console.")
            break
        elif choice == "1":
            interactive_mst()
        elif choice == "2":
            interactive_floyd_warshall()
        elif choice == "3":
            interactive_indexing()
        elif choice == "4":
            interactive_prioritization()
        elif choice == "5":
            interactive_budgeting()
        elif choice == "6":
            interactive_tsp()
        elif choice == "7":
            run_automated_pipeline()
        else:
            print("  -> Please enter a valid option between 0 and 7.")


def run_automated_pipeline() -> None:
    print("#" * 105)
    print("  ASSIGNMENT 4: ADAPTIVE NETWORK DESIGN AND OPTIMIZATION FRAMEWORK")
    print("  Course: Design and Analysis of Algorithms | Full 6-Stage End-to-End Demonstration")
    print("#" * 105)

    base_graph = demo_module_1_mst()
    demo_module_2_all_pairs_routing(base_graph)
    demo_module_3_indexing()
    demo_module_4_prioritization()
    demo_module_5_budgeting()
    demo_module_6_and_7_tsp_and_complexity(base_graph)

    print("\n" + "#" * 105)
    print("  ALL 6 ASSIGNMENT 4 MODULES EXECUTED SUCCESSFULLY.")
    print("#" * 105)


def main() -> None:
    if "--interactive" in sys.argv or "-i" in sys.argv:
        run_interactive_console()
        return

    run_automated_pipeline()

    if sys.stdin.isatty():
        try:
            ans = input("\nWould you like to launch the Interactive Viva Console to test custom inputs? [y/N]: ").strip().lower()
            if ans in ("y", "yes"):
                run_interactive_console()
        except (EOFError, KeyboardInterrupt):
            pass


if __name__ == "__main__":
    main()
