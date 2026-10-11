"""Upgrade asset domain models for capital expenditure budget allocation."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional


class AssetCategory(str, Enum):
    """Categorization of network infrastructure upgrades."""
    BANDWIDTH_TRANSIT = "BANDWIDTH_TRANSIT"    # Divisible fiber/transit lease
    CORE_CHASSIS = "CORE_CHASSIS"              # Discrete modular chassis router
    SERVER_RACK = "SERVER_RACK"                # Discrete data center compute rack
    OPTICAL_TRANSCEIVER = "OPTICAL_TRANSCEIVER"# Discrete pluggable optical module
    BATTERY_BACKUP = "BATTERY_BACKUP"          # Discrete uninterruptible power unit


@dataclass
class UpgradeItem:
    """Network upgrade proposal competing for capital expenditure budget.
    
    Attributes:
        id: Unique identifier for the proposal (e.g. 'UPG-BW-01').
        name: Human-readable asset name.
        category: Asset categorization.
        cost: Monetary expenditure required to procure the item (w_i).
        utility_value: Quantitative performance or reliability gain (v_i).
        is_divisible: Whether item can be procured in fractional units.
        target_node_id: Optional network vertex receiving the upgrade.
        metadata: Domain-specific asset parameters.
    """
    id: str
    name: str
    category: AssetCategory
    cost: float
    utility_value: float
    is_divisible: bool = False
    target_node_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("UpgradeItem id must be non-empty.")
        if self.cost <= 0.0:
            raise ValueError(f"Cost must be strictly positive, got: {self.cost}")
        if self.utility_value <= 0.0:
            raise ValueError(f"Utility value must be strictly positive, got: {self.utility_value}")

    @property
    def value_density(self) -> float:
        """Benefit-to-cost ratio (v_i / w_i)."""
        return self.utility_value / self.cost

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category.value,
            "cost": self.cost,
            "utility_value": self.utility_value,
            "value_density": self.value_density,
            "is_divisible": self.is_divisible,
            "target_node_id": self.target_node_id,
            "metadata": dict(self.metadata),
        }

