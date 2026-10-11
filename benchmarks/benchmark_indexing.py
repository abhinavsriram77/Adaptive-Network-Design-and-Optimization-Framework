"""Comparative benchmark comparing in-memory Red-Black Tree vs. disk-backed B-Tree."""

from __future__ import annotations

import random
import sys
import time
from pathlib import Path

# Add project root to sys.path
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from indexing.b_tree import BTree
from indexing.red_black_tree import RedBlackTree
from utils.telemetry import profile_execution


def run_indexing_benchmark() -> None:
    print("=" * 85)
    print("DUAL-TIER INDEXING BENCHMARK: RED-BLACK TREE (RAM) VS. B-TREE (DISK BLOCKS)")
    print("=" * 85)

    n_keys = 2000
    rng = random.Random(999)
    keys = list(range(1, n_keys + 1))
    rng.shuffle(keys)

    # 1. Benchmark Red-Black Tree (In-Memory)
    rbt = RedBlackTree()
    with profile_execution() as rbt_insert_prof:
        for k in keys:
            rbt.insert(k, f"payload_{k}")

    # Search benchmark
    query_sample = rng.sample(keys, 500)
    t0 = time.perf_counter()
    for q in query_sample:
        _ = rbt.search(q)
    rbt_search_ms = (time.perf_counter() - t0) * 1000.0

    # 2. Benchmark B-Tree (Order t=3)
    btree_t3 = BTree(t=3)
    with profile_execution() as btree_insert_prof:
        for k in keys:
            btree_t3.insert(k, f"payload_{k}")

    t0 = time.perf_counter()
    for q in query_sample:
        _ = btree_t3.search(q)
    btree_search_ms = (time.perf_counter() - t0) * 1000.0

    # 3. Benchmark B-Tree (Order t=6, larger block simulation)
    btree_t6 = BTree(t=6)
    for k in keys:
        btree_t6.insert(k, f"payload_{k}")

    t0 = time.perf_counter()
    for q in query_sample:
        _ = btree_t6.search(q)
    btree_t6_search_ms = (time.perf_counter() - t0) * 1000.0

    # Display results
    print(f"Dataset Size: {n_keys:,} unique telemetry records | Queries Sampled: 500")
    print("-" * 85)
    header = f"{'Index Structure':<22} | {'Insert (ms)':<12} | {'Search 500 (ms)':<16} | {'Structural Events':<18} | {'Simulated I/O':<14}"
    print(header)
    print("-" * 85)

    rbt_events = f"{rbt.rotations} rotations"
    print(
        f"{'Red-Black Tree (RAM)':<22} | {rbt_insert_prof.elapsed_time_ms:<12.2f} | {rbt_search_ms:<16.3f} | {rbt_events:<18} | {'N/A (In-Memory)':<14}"
    )

    btree_events = f"{btree_t3.splits} splits"
    btree_io = f"{btree_t3.disk_reads}R / {btree_t3.disk_writes}W"
    print(
        f"{'B-Tree (Order t=3)':<22} | {btree_insert_prof.elapsed_time_ms:<12.2f} | {btree_search_ms:<16.3f} | {btree_events:<18} | {btree_io:<14}"
    )

    btree_t6_events = f"{btree_t6.splits} splits"
    btree_t6_io = f"{btree_t6.disk_reads}R / {btree_t6.disk_writes}W"
    print(
        f"{'B-Tree (Order t=6)':<22} | {'--':<12} | {btree_t6_search_ms:<16.3f} | {btree_t6_events:<18} | {btree_t6_io:<14}"
    )

    print("-" * 85)
    print("Telemetry Validation:")
    rbt_valid, rbt_msg = rbt.validate_invariants()
    b3_valid, b3_msg = btree_t3.validate_invariants()
    b6_valid, b6_msg = btree_t6.validate_invariants()
    print(f" - Red-Black Tree Invariants: {'VALID' if rbt_valid else 'FAILED'} ({rbt_msg})")
    print(f" - B-Tree (t=3) Invariants:   {'VALID' if b3_valid else 'FAILED'} ({b3_msg})")
    print(f" - B-Tree (t=6) Invariants:   {'VALID' if b6_valid else 'FAILED'} ({b6_msg})")
    print("=" * 85)


if __name__ == "__main__":
    run_indexing_benchmark()
