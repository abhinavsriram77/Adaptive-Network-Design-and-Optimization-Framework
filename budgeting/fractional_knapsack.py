"""Fractional Knapsack greedy optimization solver for divisible network upgrades."""

from __future__ import annotations

import time
from typing import List

from budgeting.base import AllocationResult, AllocationSlice, BaseKnapsackSolver
from budgeting.item import UpgradeItem


class FractionalKnapsackSolver(BaseKnapsackSolver):
    """Greedy solver for divisible assets (bandwidth transit leases) in O(n log n) time."""

    @property
    def name(self) -> str:
        return "Fractional Knapsack (Greedy Value-Density Sorting)"

    def solve(self, items: List[UpgradeItem], budget: float) -> AllocationResult:
        """Allocate budget greedily in descending order of value density (v_i / w_i).
        
        Args:
            items: Candidate UpgradeItem proposals.
            budget: Maximum expenditure constraint (W).
            
        Returns:
            AllocationResult detailing procured items and fractional slices.
        """
        start_time = time.perf_counter()

        if budget <= 0.0 or not items:
            return AllocationResult(
                total_cost=0.0,
                total_value=0.0,
                budget_limit=max(0.0, budget),
                slices=[],
                solver_name=self.name,
                execution_time_ms=(time.perf_counter() - start_time) * 1000.0,
                operations_count=0,
                metadata={"items_considered": len(items)},
            )

        # 1. Sort items descending by value density: O(n log n)
        sort_start = time.perf_counter()
        sorted_items = sorted(items, key=lambda x: x.value_density, reverse=True)
        n = len(sorted_items)
        comparisons = int(n * (n.bit_length() - 1)) if n > 1 else 0

        slices: List[AllocationSlice] = []
        total_cost = 0.0
        total_value = 0.0
        remaining_budget = budget
        epsilon = 1e-9

        for item in sorted_items:
            if remaining_budget <= epsilon:
                break

            if item.cost <= remaining_budget + epsilon:
                # Procure entire item
                slices.append(
                    AllocationSlice(
                        item=item,
                        fraction=1.0,
                        allocated_cost=item.cost,
                        achieved_value=item.utility_value,
                    )
                )
                total_cost += item.cost
                total_value += item.utility_value
                remaining_budget = max(0.0, remaining_budget - item.cost)
            else:
                # Can only take fraction if item allows divisibility
                if item.is_divisible:
                    fraction = remaining_budget / item.cost
                    alloc_cost = remaining_budget
                    achieved_val = fraction * item.utility_value

                    slices.append(
                        AllocationSlice(
                            item=item,
                            fraction=fraction,
                            allocated_cost=alloc_cost,
                            achieved_value=achieved_val,
                        )
                    )
                    total_cost += alloc_cost
                    total_value += achieved_val
                    remaining_budget = 0.0
                    break

        exec_time_ms = (time.perf_counter() - start_time) * 1000.0

        return AllocationResult(
            total_cost=total_cost,
            total_value=total_value,
            budget_limit=budget,
            slices=slices,
            solver_name=self.name,
            execution_time_ms=exec_time_ms,
            operations_count=comparisons,
            metadata={
                "items_considered": n,
                "items_allocated": len(slices),
                "fractional_items": sum(1 for s in slices if s.fraction < 1.0 - epsilon),
            },
        )

