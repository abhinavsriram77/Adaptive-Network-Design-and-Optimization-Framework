"""Abstract base contracts and result representations for budget allocation solvers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List

from budgeting.item import UpgradeItem


@dataclass
class AllocationSlice:
    """Allocated portion of an individual upgrade item.
    
    Attributes:
        item: UpgradeItem reference.
        fraction: Fraction acquired (1.0 for whole discrete, in [0.0, 1.0] for divisible).
        allocated_cost: Cost incurred for this fraction (fraction * item.cost).
        achieved_value: Utility gained from this fraction (fraction * item.utility_value).
    """
    item: UpgradeItem
    fraction: float
    allocated_cost: float
    achieved_value: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "item_id": self.item.id,
            "item_name": self.item.name,
            "category": self.item.category.value,
            "fraction": round(self.fraction, 4),
            "allocated_cost": round(self.allocated_cost, 2),
            "achieved_value": round(self.achieved_value, 2),
            "is_divisible": self.item.is_divisible,
        }


@dataclass
class AllocationResult:
    """Optimal procurement portfolio output under budget constraints.
    
    Attributes:
        total_cost: Sum of expenditure across all acquired items.
        total_value: Total achieved quantitative utility.
        budget_limit: Total budget capacity constraint (W).
        slices: List of AllocationSlice records detailing procured assets.
        solver_name: Identifier of the algorithm used.
        execution_time_ms: Runtime in milliseconds.
        operations_count: Algorithmic operations (comparisons, table state cells).
        metadata: Domain-specific diagnostic telemetry.
    """
    total_cost: float
    total_value: float
    budget_limit: float
    slices: List[AllocationSlice]
    solver_name: str
    execution_time_ms: float = 0.0
    operations_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def unused_budget(self) -> float:
        """Surplus unallocated budget remainder."""
        return max(0.0, self.budget_limit - self.total_cost)

    @property
    def budget_utilization(self) -> float:
        """Fraction of total budget allocated [0.0, 1.0]."""
        if self.budget_limit <= 0.0:
            return 0.0
        return min(1.0, self.total_cost / self.budget_limit)

    @property
    def overall_roi(self) -> float:
        """Overall return on investment: total value gained per unit currency spent."""
        if self.total_cost <= 0.0:
            return 0.0
        return self.total_value / self.total_cost

    def to_dict(self) -> Dict[str, Any]:
        return {
            "solver_name": self.solver_name,
            "total_cost": round(self.total_cost, 2),
            "total_value": round(self.total_value, 2),
            "budget_limit": round(self.budget_limit, 2),
            "unused_budget": round(self.unused_budget, 2),
            "budget_utilization": round(self.budget_utilization, 4),
            "overall_roi": round(self.overall_roi, 4),
            "items_count": len(self.slices),
            "execution_time_ms": self.execution_time_ms,
            "operations_count": self.operations_count,
            "slices": [s.to_dict() for s in self.slices],
            "metadata": dict(self.metadata),
        }


class BaseKnapsackSolver(ABC):
    """Abstract interface for knapsack budget allocation solvers."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Descriptive solver identifier."""
        pass

    @abstractmethod
    def solve(self, items: List[UpgradeItem], budget: float) -> AllocationResult:
        """Solve knapsack budget allocation for the candidate item catalog."""
        pass

