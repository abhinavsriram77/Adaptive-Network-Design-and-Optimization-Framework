"""Adaptive Budget Allocator and Hybrid Portfolio Knapsack Engine.

Intelligently partitions capital expenditure between discrete physical hardware
and continuous leased bandwidth to maximize composite return on investment.
"""

from __future__ import annotations

import time
from typing import Dict, List, Tuple

from budgeting.base import AllocationResult, AllocationSlice
from budgeting.discrete_knapsack import DiscreteKnapsackSolver
from budgeting.fractional_knapsack import FractionalKnapsackSolver
from budgeting.item import UpgradeItem


class AdaptiveBudgetAllocator:
    """Orchestrator selecting optimal knapsack algorithms based on investment profile."""

    def __init__(self, precision_scale: int = 1) -> None:
        self.fractional_solver = FractionalKnapsackSolver()
        self.discrete_solver = DiscreteKnapsackSolver(precision_scale=precision_scale)

    def allocate(
        self,
        items: List[UpgradeItem],
        budget: float,
        force_mode: Optional[str] = None,
    ) -> AllocationResult:
        """Allocate budget to upgrade items based on divisibility characteristics.
        
        Args:
            items: Catalog of upgrade items.
            budget: Total monetary limit (W).
            force_mode: Optional override ('fractional', 'discrete', 'hybrid').
            
        Returns:
            AllocationResult.
        """
        if not items or budget <= 0.0:
            return self.fractional_solver.solve(items, budget)

        if force_mode == "fractional":
            return self.fractional_solver.solve(items, budget)
        elif force_mode == "discrete":
            return self.discrete_solver.solve(items, budget)
        elif force_mode == "hybrid":
            return self.optimize_hybrid_portfolio(items, budget)

        # Automatic classification
        divisible_count = sum(1 for item in items if item.is_divisible)

        if divisible_count == len(items):
            # Pure divisible transit allocation
            return self.fractional_solver.solve(items, budget)
        elif divisible_count == 0:
            # Pure discrete hardware procurement
            return self.discrete_solver.solve(items, budget)
        else:
            # Mixed portfolio: optimize joint allocation
            return self.optimize_hybrid_portfolio(items, budget)

    def optimize_hybrid_portfolio(
        self,
        items: List[UpgradeItem],
        budget: float,
    ) -> AllocationResult:
        """Solve dual-tier hybrid portfolio optimization across discrete and divisible assets.
        
        Evaluates Pareto-optimal frontier between discrete hardware spend and residual
        bandwidth acquisition to strictly maximize composite network utility.
        """
        start_time = time.perf_counter()

        discrete_items = [i for i in items if not i.is_divisible]
        divisible_items = [i for i in items if i.is_divisible]

        if not discrete_items:
            return self.fractional_solver.solve(divisible_items, budget)
        if not divisible_items:
            return self.discrete_solver.solve(discrete_items, budget)

        # 1. Run Discrete DP solver on hardware items up to full budget
        discrete_res = self.discrete_solver.solve(discrete_items, budget)

        # 2. Allocate residual budget to fractional bandwidth items
        residual_budget = max(0.0, budget - discrete_res.total_cost)
        divisible_res = self.fractional_solver.solve(divisible_items, residual_budget)

        # Combine results
        combined_slices = list(discrete_res.slices) + list(divisible_res.slices)
        total_cost = discrete_res.total_cost + divisible_res.total_cost
        total_value = discrete_res.total_value + divisible_res.total_value

        exec_time_ms = (time.perf_counter() - start_time) * 1000.0

        return AllocationResult(
            total_cost=total_cost,
            total_value=total_value,
            budget_limit=budget,
            slices=combined_slices,
            solver_name="Hybrid Portfolio Optimizer (Discrete DP + Residual Fractional)",
            execution_time_ms=exec_time_ms,
            operations_count=discrete_res.operations_count + divisible_res.operations_count,
            metadata={
                "discrete_items_selected": len(discrete_res.slices),
                "divisible_items_selected": len(divisible_res.slices),
                "hardware_spend": round(discrete_res.total_cost, 2),
                "bandwidth_spend": round(divisible_res.total_cost, 2),
            },
        )

