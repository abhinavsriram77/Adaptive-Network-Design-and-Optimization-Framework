"""Comparative benchmark for Fractional Knapsack vs. 0/1 Knapsack DP solvers."""

from __future__ import annotations

import random
import sys
from pathlib import Path

# Add project root to sys.path
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from budgeting.discrete_knapsack import DiscreteKnapsackSolver
from budgeting.fractional_knapsack import FractionalKnapsackSolver
from budgeting.item import AssetCategory, UpgradeItem


def run_budgeting_benchmark() -> None:
    print("=" * 88)
    print("UPGRADE BUDGET ALLOCATION BENCHMARK: FRACTIONAL (GREEDY) VS. 0/1 (DP)")
    print("=" * 88)

    rng = random.Random(42)
    item_counts = [50, 150, 300]
    budget = 500.0

    frac_solver = FractionalKnapsackSolver()
    discrete_solver = DiscreteKnapsackSolver(precision_scale=1)

    header = f"{'Item Count':<12} | {'Budget':<8} | {'Fractional Time':<18} | {'0/1 DP Time':<16} | {'Frac Value':<12} | {'0/1 Value':<10}"
    print(header)
    print("-" * 88)

    for n in item_counts:
        # Generate random upgrade items
        items = []
        for i in range(n):
            c = round(rng.uniform(5.0, 50.0), 1)
            v = round(rng.uniform(10.0, 120.0), 1)
            items.append(
                UpgradeItem(
                    id=f"ITEM-{i:04d}",
                    name=f"Proposal {i}",
                    category=AssetCategory.BANDWIDTH_TRANSIT if i % 2 == 0 else AssetCategory.CORE_CHASSIS,
                    cost=c,
                    utility_value=v,
                    is_divisible=True,  # Set divisible for fractional solver
                )
            )

        # Fractional Knapsack (Greedy)
        res_frac = frac_solver.solve(items, budget=budget)

        # Discrete 0/1 Knapsack (DP)
        discrete_items = [
            UpgradeItem(
                id=item.id,
                name=item.name,
                category=item.category,
                cost=item.cost,
                utility_value=item.utility_value,
                is_divisible=False,
            )
            for item in items
        ]
        res_disc = discrete_solver.solve(discrete_items, budget=budget)

        print(
            f"{n:<12} | {budget:<8.0f} | {res_frac.execution_time_ms:<14.3f} ms | {res_disc.execution_time_ms:<12.3f} ms | {res_frac.total_value:<12.1f} | {res_disc.total_value:<10.1f}"
        )

    print("-" * 88)
    print("Notes:")
    print(" - Fractional Knapsack always yields an upper bound on utility (V_frac >= V_01).")
    print(" - Fractional Knapsack scales with O(n log n) sorting, while 0/1 DP scales with O(n · W).")
    print("=" * 88)


if __name__ == "__main__":
    run_budgeting_benchmark()

