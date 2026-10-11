"""Node domain models for heterogeneous network infrastructure.

Represents Network Hubs, Data Centers, and IoT Gateways with workload,
geographic, and hardware capacity metrics.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional


class NodeType(str, Enum):
    """Categorization of network topology vertices."""
    NETWORK_HUB = "NETWORK_HUB"
    DATA_CENTER = "DATA_CENTER"
    IOT_GATEWAY = "IOT_GATEWAY"


@dataclass
class Node:
    """Base class for vertices in the network optimization framework.
    
    Attributes:
        id: Unique identifier for the node.
        name: Human-readable label for the node.
        node_type: Topological category (Hub, Data Center, IoT Gateway).
        latitude: Geographic latitude in decimal degrees [-90.0, 90.0].
        longitude: Geographic longitude in decimal degrees [-180.0, 180.0].
        processing_capacity: Computational capacity (e.g., GFLOPS or MIPS).
        memory_capacity_mb: Working memory capacity in megabytes.
        is_active: Operational status flag.
        metadata: Arbitrary domain-specific metadata.
    """
    id: str
    name: str
    node_type: NodeType
    latitude: float = 0.0
    longitude: float = 0.0
    processing_capacity: float = 100.0
    memory_capacity_mb: float = 1024.0
    is_active: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id or not isinstance(self.id, str):
            raise ValueError(f"Node id must be a non-empty string, got: {self.id!r}")
        if not (-90.0 <= self.latitude <= 90.0):
            raise ValueError(f"Latitude must be within [-90.0, 90.0], got: {self.latitude}")
        if not (-180.0 <= self.longitude <= 180.0):
            raise ValueError(f"Longitude must be within [-180.0, 180.0], got: {self.longitude}")
        if self.processing_capacity < 0.0:
            raise ValueError(f"Processing capacity must be non-negative, got: {self.processing_capacity}")
        if self.memory_capacity_mb < 0.0:
            raise ValueError(f"Memory capacity must be non-negative, got: {self.memory_capacity_mb}")

    def __hash__(self) -> int:
        return hash(self.id)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Node):
            return self.id == other.id
        return False

    def to_dict(self) -> Dict[str, Any]:
        """Serialize node attributes to a dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "node_type": self.node_type.value,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "processing_capacity": self.processing_capacity,
            "memory_capacity_mb": self.memory_capacity_mb,
            "is_active": self.is_active,
            "metadata": dict(self.metadata),
        }


@dataclass
class NetworkHub(Node):
    """High-throughput aggregation routing hub interconnecting regions.
    
    Attributes:
        switching_capacity_gbps: Maximum total packet forwarding rate.
        max_connected_ports: Number of available physical transceiver ports.
    """
    node_type: NodeType = field(default=NodeType.NETWORK_HUB, init=False)
    switching_capacity_gbps: float = 400.0
    max_connected_ports: int = 64

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.switching_capacity_gbps < 0.0:
            raise ValueError(f"Switching capacity must be non-negative, got: {self.switching_capacity_gbps}")
        if self.max_connected_ports < 1:
            raise ValueError(f"Max ports must be at least 1, got: {self.max_connected_ports}")

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "switching_capacity_gbps": self.switching_capacity_gbps,
            "max_connected_ports": self.max_connected_ports,
        })
        return data


@dataclass
class DataCenter(Node):
    """Core computing and storage facility hosting primary workloads.
    
    Attributes:
        server_rack_count: Number of compute racks deployed.
        storage_capacity_tb: Total raw storage capacity in terabytes.
        tier_rating: Uptime Institute Data Center Tier standard (1 to 4).
    """
    node_type: NodeType = field(default=NodeType.DATA_CENTER, init=False)
    server_rack_count: int = 128
    storage_capacity_tb: float = 1000.0
    tier_rating: int = 4

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.server_rack_count < 1:
            raise ValueError(f"Server rack count must be >= 1, got: {self.server_rack_count}")
        if self.storage_capacity_tb < 0.0:
            raise ValueError(f"Storage capacity must be >= 0, got: {self.storage_capacity_tb}")
        if not (1 <= self.tier_rating <= 4):
            raise ValueError(f"Tier rating must be between 1 and 4, got: {self.tier_rating}")

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "server_rack_count": self.server_rack_count,
            "storage_capacity_tb": self.storage_capacity_tb,
            "tier_rating": self.tier_rating,
        })
        return data


@dataclass
class IoTGateway(Node):
    """Edge collector aggregating telemetry and sensor feeds.
    
    Attributes:
        sensor_channel_count: Ingestion channels for field telemetry.
        battery_powered: Whether the node operates on battery.
        battery_level_pct: Remaining battery percentage [0.0, 100.0] or None if mains-powered.
        duty_cycle_pct: Active awake cycle ratio [0.0, 100.0].
    """
    node_type: NodeType = field(default=NodeType.IOT_GATEWAY, init=False)
    sensor_channel_count: int = 16
    battery_powered: bool = False
    battery_level_pct: Optional[float] = None
    duty_cycle_pct: float = 100.0

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.sensor_channel_count < 0:
            raise ValueError(f"Sensor channels must be non-negative, got: {self.sensor_channel_count}")
        if not (0.0 <= self.duty_cycle_pct <= 100.0):
            raise ValueError(f"Duty cycle must be in [0.0, 100.0], got: {self.duty_cycle_pct}")
        if self.battery_powered and self.battery_level_pct is not None:
            if not (0.0 <= self.battery_level_pct <= 100.0):
                raise ValueError(f"Battery level must be in [0.0, 100.0], got: {self.battery_level_pct}")

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "sensor_channel_count": self.sensor_channel_count,
            "battery_powered": self.battery_powered,
            "battery_level_pct": self.battery_level_pct,
            "duty_cycle_pct": self.duty_cycle_pct,
        })
        return data
