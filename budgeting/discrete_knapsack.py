"""0/1 Knapsack dynamic programming solver for indivisible hardware equipment."""

from __future__ import annotations

import time
from typing import List, Tuple

from budgeting.base import AllocationResult, AllocationSlice, BaseKnapsackSolver
from budgeting.item import UpgradeItem


class DiscreteKnapsackSolver(BaseKnapsackSolver):
    """Dynamic programming 0/1 knapsack solver with state backtracking."""

    def __init__(self, precision_scale: int = 1) -> None:
        """Initialize discrete solver.
        
        Args:
            precision_scale: Multiplier for discretizing floating-point costs into integer DP indices
                            (e.g., 1 for integer budgets, 100 for cents resolution).
        """
        if precision_scale < 1:
            raise ValueError(f"precision_scale must be >= 1, got: {precision_scale}")
        self.precision_scale = precision_scale

    @property
    def name(self) -> str:
        return "0/1 Knapsack (Dynamic Programming with State Backtracking)"

    def solve(self, items: List[UpgradeItem], budget: float) -> AllocationResult:
        """Solve 0/1 knapsack using DP table recurrence and backtracking.
        
        Args:
            items: Candidate UpgradeItem proposals (discrete x_i in {0, 1}).
            budget: Maximum monetary budget limit (W).
            
        Returns:
            AllocationResult containing the exact subset of chosen items.
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

        n = len(items)
        scale = self.precision_scale
        w_limit = int(round(budget * scale))

        # Discretize item weights
        scaled_weights = [int(round(item.cost * scale)) for item in items]
        values = [item.utility_value for item in items]

        # 1. Build 2D DP Table: DP[i][w] = max value using subset of first i items with capacity w
        # Dimension: (n + 1) x (w_limit + 1)
        dp: List[List[float]] = [[0.0] * (w_limit + 1) for _ in range(n + 1)]
        operations = 0

        for i in range(1, n + 1):
            w_i = scaled_weights[i - 1]
            v_i = values[i - 1]
            dp_prev = dp[i - 1]
            dp_curr = dp[i]

            for w in range(w_limit + 1):
                operations += 1
                if w_i > w:
                    dp_curr[w] = dp_prev[w]
                else:
                    val_without = dp_prev[w]
                    val_with = dp_prev[w - w_i] + v_i
                    dp_curr[w] = val_with if val_with > val_without else val_without

        # 2. State Backtracking to reconstruct chosen items
        slices: List[AllocationSlice] = []
        curr_w = w_limit
        total_cost = 0.0
        total_value = dp[n][w_limit]

        for i in range(n, 0, -1):
            if dp[i][curr_w] != dp[i - 1][curr_w]:
                chosen_item = items[i - 1]
                slices.append(
                    AllocationSlice(
                        item=chosen_item,
                        fraction=1.0,
                        allocated_cost=chosen_item.cost,
                        achieved_value=chosen_item.utility_value,
                    )
                )
                total_cost += chosen_item.cost
                curr_w -= scaled_weights[i - 1]

        # Reverse to restore original catalog sequence
        slices.reverse()
        exec_time_ms = (time.perf_counter() - start_time) * 1000.0

        return AllocationResult(
            total_cost=total_cost,
            total_value=total_value,
            budget_limit=budget,
            slices=slices,
            solver_name=self.name,
            execution_time_ms=exec_time_ms,
            operations_count=operations,
            metadata={
                "items_considered": n,
                "items_selected": len(slices),
                "dp_table_cells": (n + 1) * (w_limit + 1),
                "precision_scale": scale,
            },
        )

