"""Unit tests for Fractional Knapsack, 0/1 Knapsack DP, and Adaptive Budget Allocator."""

import math
import sys
from pathlib import Path

# Add project root to sys.path
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import pytest
from budgeting.discrete_knapsack import DiscreteKnapsackSolver
from budgeting.fractional_knapsack import FractionalKnapsackSolver
from budgeting.item import AssetCategory, UpgradeItem
from budgeting.selector import AdaptiveBudgetAllocator


def test_upgrade_item_properties():
    item = UpgradeItem(
        id="UPG-01",
        name="100G Transit Lease",
        category=AssetCategory.BANDWIDTH_TRANSIT,
        cost=20.0,
        utility_value=100.0,
        is_divisible=True,
    )
    assert item.id == "UPG-01"
    assert item.value_density == 5.0
    assert item.is_divisible is True

    # Validation errors
    with pytest.raises(ValueError):
        UpgradeItem(id="", name="Invalid", category=AssetCategory.CORE_CHASSIS, cost=10.0, utility_value=10.0)
    with pytest.raises(ValueError):
        UpgradeItem(id="X", name="Invalid Cost", category=AssetCategory.CORE_CHASSIS, cost=-5.0, utility_value=10.0)


def test_fractional_knapsack_greedy_optimality():
    # Classic textbook scenario:
    # Item 1: w=10, v=60  (density = 6.0)
    # Item 2: w=20, v=100 (density = 5.0)
    # Item 3: w=30, v=120 (density = 4.0)
    # Budget = 50
    # Expected: Take 100% of Item 1, 100% of Item 2, and 20/30 (66.67%) of Item 3.
    # Total Value = 60 + 100 + (2/3 * 120) = 240.0, Total Cost = 50.0
    items = [
        UpgradeItem("I1", "Item 1", AssetCategory.BANDWIDTH_TRANSIT, cost=10.0, utility_value=60.0, is_divisible=True),
        UpgradeItem("I2", "Item 2", AssetCategory.BANDWIDTH_TRANSIT, cost=20.0, utility_value=100.0, is_divisible=True),
        UpgradeItem("I3", "Item 3", AssetCategory.BANDWIDTH_TRANSIT, cost=30.0, utility_value=120.0, is_divisible=True),
    ]

    solver = FractionalKnapsackSolver()
    result = solver.solve(items, budget=50.0)

    assert math.isclose(result.total_cost, 50.0)
    assert math.isclose(result.total_value, 240.0)
    assert math.isclose(result.budget_utilization, 1.0)
    assert len(result.slices) == 3

    # Check slice fractions
    s1, s2, s3 = result.slices
    assert s1.item.id == "I1" and math.isclose(s1.fraction, 1.0)
    assert s2.item.id == "I2" and math.isclose(s2.fraction, 1.0)
    assert s3.item.id == "I3" and math.isclose(s3.fraction, 20.0 / 30.0)


def test_fractional_knapsack_edge_cases():
    solver = FractionalKnapsackSolver()
    items = [
        UpgradeItem("I1", "Item 1", AssetCategory.BANDWIDTH_TRANSIT, cost=10.0, utility_value=50.0, is_divisible=True),
    ]

    # Zero budget
    res_zero = solver.solve(items, budget=0.0)
    assert res_zero.total_cost == 0.0
    assert res_zero.total_value == 0.0
    assert len(res_zero.slices) == 0

    # Budget exceeds all items
    res_large = solver.solve(items, budget=100.0)
    assert res_large.total_cost == 10.0
    assert res_large.total_value == 50.0
    assert math.isclose(res_large.unused_budget, 90.0)


def test_discrete_knapsack_01_dp():
    # Items (discrete hardware):
    # I1: cost=2, value=3
    # I2: cost=3, value=4
    # I3: cost=4, value=5
    # I4: cost=5, value=6
    # Budget = 5
    # Combinations: {I1, I2} cost=5, val=7. {I4} cost=5, val=6. {I1, I3} cost=6 > 5.
    # Optimal: {I1, I2} with value=7, cost=5
    items = [
        UpgradeItem("I1", "Switch A", AssetCategory.OPTICAL_TRANSCEIVER, cost=2.0, utility_value=3.0, is_divisible=False),
        UpgradeItem("I2", "Switch B", AssetCategory.OPTICAL_TRANSCEIVER, cost=3.0, utility_value=4.0, is_divisible=False),
        UpgradeItem("I3", "Switch C", AssetCategory.OPTICAL_TRANSCEIVER, cost=4.0, utility_value=5.0, is_divisible=False),
        UpgradeItem("I4", "Switch D", AssetCategory.OPTICAL_TRANSCEIVER, cost=5.0, utility_value=6.0, is_divisible=False),
    ]

    solver = DiscreteKnapsackSolver(precision_scale=1)
    result = solver.solve(items, budget=5.0)

    assert math.isclose(result.total_cost, 5.0)
    assert math.isclose(result.total_value, 7.0)
    assert len(result.slices) == 2

    chosen_ids = {s.item.id for s in result.slices}
    assert chosen_ids == {"I1", "I2"}
    # Slices must be whole (fraction == 1.0)
    for s in result.slices:
        assert s.fraction == 1.0


def test_discrete_knapsack_insufficient_budget():
    items = [
        UpgradeItem("HW-01", "Core Chassis", AssetCategory.CORE_CHASSIS, cost=50.0, utility_value=100.0, is_divisible=False),
    ]
    solver = DiscreteKnapsackSolver()
    result = solver.solve(items, budget=20.0)

    assert result.total_cost == 0.0
    assert result.total_value == 0.0
    assert len(result.slices) == 0


def test_adaptive_budget_allocator_dispatch():
    allocator = AdaptiveBudgetAllocator(precision_scale=1)

    divisible_items = [
        UpgradeItem("BW1", "Transit 1", AssetCategory.BANDWIDTH_TRANSIT, cost=10.0, utility_value=50.0, is_divisible=True),
        UpgradeItem("BW2", "Transit 2", AssetCategory.BANDWIDTH_TRANSIT, cost=20.0, utility_value=80.0, is_divisible=True),
    ]
    discrete_items = [
        UpgradeItem("HW1", "Server 1", AssetCategory.SERVER_RACK, cost=15.0, utility_value=40.0, is_divisible=False),
        UpgradeItem("HW2", "Server 2", AssetCategory.SERVER_RACK, cost=25.0, utility_value=70.0, is_divisible=False),
    ]

    # 1. Pure divisible auto-dispatch -> Fractional Knapsack
    res_div = allocator.allocate(divisible_items, budget=15.0)
    assert "Fractional" in res_div.solver_name
    assert math.isclose(res_div.total_cost, 15.0)

    # 2. Pure discrete auto-dispatch -> 0/1 Knapsack
    res_disc = allocator.allocate(discrete_items, budget=20.0)
    assert "0/1" in res_disc.solver_name
    assert math.isclose(res_disc.total_cost, 15.0)  # HW1 fits (cost 15), HW2 requires 25

    # 3. Mixed portfolio -> Hybrid Optimizer
    mixed_catalog = divisible_items + discrete_items
    # Budget = 30. Discrete HW1 (cost 15, val 40) is picked, leaving 15 residual for BW1 (cost 10, val 50) + fraction of BW2 (cost 5, val 20)
    res_hybrid = allocator.allocate(mixed_catalog, budget=30.0)
    assert "Hybrid" in res_hybrid.solver_name
    assert math.isclose(res_hybrid.total_cost, 30.0)
    assert res_hybrid.total_value > 0.0


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))

