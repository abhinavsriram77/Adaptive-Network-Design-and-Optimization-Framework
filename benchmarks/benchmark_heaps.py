"""Comparative benchmark comparing Binomial Heap vs. Fibonacci Heap under heavy escalation."""

from __future__ import annotations

import random
import sys
import time
from pathlib import Path

# Add project root to sys.path
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from prioritization.binomial_heap import BinomialHeap
from prioritization.fibonacci_heap import FibonacciHeap
from utils.telemetry import profile_execution


def run_heap_benchmark() -> None:
    print("=" * 90)
    print("INCIDENT PRIORITY QUEUE BENCHMARK: BINOMIAL HEAP VS. FIBONACCI HEAP")
    print("=" * 90)

    n_incidents = 2000
    n_escalations = 1000

    rng = random.Random(42)
    initial_priorities = [round(rng.uniform(10.0, 500.0), 2) for _ in range(n_incidents)]

    # 1. Benchmark Binomial Heap
    bin_heap = BinomialHeap()
    bin_nodes = []

    with profile_execution() as bin_prof:
        # Ingestion
        t_ins0 = time.perf_counter()
        for i, prio in enumerate(initial_priorities):
            node = bin_heap.insert(prio, f"inc_{i}")
            bin_nodes.append(node)
        bin_ins_time = (time.perf_counter() - t_ins0) * 1000.0

        # Heavy dynamic escalations (decrease_key)
        t_dec0 = time.perf_counter()
        targets = rng.sample(bin_nodes, n_escalations)
        for node in targets:
            new_p = max(0.5, node.key - rng.uniform(5.0, 20.0))
            bin_heap.decrease_key(node, new_p)
        bin_dec_time = (time.perf_counter() - t_dec0) * 1000.0

        # Drain queue
        t_ext0 = time.perf_counter()
        while not bin_heap.is_empty():
            _ = bin_heap.extract_min()
        bin_ext_time = (time.perf_counter() - t_ext0) * 1000.0

    # 2. Benchmark Fibonacci Heap
    fib_heap = FibonacciHeap()
    fib_nodes = []

    with profile_execution() as fib_prof:
        # Ingestion (O(1) amortized)
        t_ins0 = time.perf_counter()
        for i, prio in enumerate(initial_priorities):
            node = fib_heap.insert(prio, f"inc_{i}")
            fib_nodes.append(node)
        fib_ins_time = (time.perf_counter() - t_ins0) * 1000.0

        # Heavy dynamic escalations (O(1) amortized cascading cuts)
        t_dec0 = time.perf_counter()
        targets = rng.sample(fib_nodes, n_escalations)
        for node in targets:
            new_p = max(0.5, node.key - rng.uniform(5.0, 20.0))
            fib_heap.decrease_key(node, new_p)
        fib_dec_time = (time.perf_counter() - t_dec0) * 1000.0

        # Drain queue
        t_ext0 = time.perf_counter()
        while not fib_heap.is_empty():
            _ = fib_heap.extract_min()
        fib_ext_time = (time.perf_counter() - t_ext0) * 1000.0

    # Display results
    print(f"Workload Profile: {n_incidents:,} Insertions | {n_escalations:,} Dynamic Escalations | {n_incidents:,} Extractions")
    print("-" * 90)
    header = f"{'Queue Architecture':<22} | {'Insert (ms)':<12} | {'Escalate (ms)':<14} | {'Extract (ms)':<13} | {'Total Time (ms)':<16}"
    print(header)
    print("-" * 90)

    print(
        f"{'Binomial Heap':<22} | {bin_ins_time:<12.2f} | {bin_dec_time:<14.2f} | {bin_ext_time:<13.2f} | {bin_prof.elapsed_time_ms:<16.2f}"
    )
    print(
        f"{'Fibonacci Heap':<22} | {fib_ins_time:<12.2f} | {fib_dec_time:<14.2f} | {fib_ext_time:<13.2f} | {fib_prof.elapsed_time_ms:<16.2f}"
    )

    print("-" * 90)
    print("Algorithmic Operations Telemetry:")
    print(f" - Binomial Heap:  Comparisons={bin_heap.telemetry.comparisons:,} | Unions={bin_heap.telemetry.unions:,}")
    print(f" - Fibonacci Heap: Comparisons={fib_heap.telemetry.comparisons:,} | Marked Nodes Count={fib_heap.marked_count}")
    print("=" * 90)


if __name__ == "__main__":
    run_heap_benchmark()

