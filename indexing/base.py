"""Abstract base contracts and data records for network storage indexing."""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional


class WorkloadType(str, Enum):
    """Categorization of incoming telemetry data operations."""
    VOLATILE_TELEMETRY = "VOLATILE_TELEMETRY"  # Low-latency, in-memory volatile lookups
    HISTORICAL_LOGS = "HISTORICAL_LOGS"        # Batch persistent disk block storage


@dataclass
class TelemetryRecord:
    """Network node operational telemetry record.
    
    Attributes:
        node_id: Originating network vertex ID.
        metric_name: Metric identifier (e.g., 'cpu_utilization', 'ingress_mbps').
        value: Numeric observation measurement.
        timestamp_ns: Nanosecond timestamp of telemetry capture.
        metadata: Domain-specific telemetry attributes.
    """
    node_id: str
    metric_name: str
    value: float
    timestamp_ns: int = field(default_factory=time.time_ns)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def composite_key(self) -> str:
        """Standardized unique key combining timestamp and node identifier."""
        return f"{self.timestamp_ns:020d}:{self.node_id}:{self.metric_name}"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id,
            "metric_name": self.metric_name,
            "value": self.value,
            "timestamp_ns": self.timestamp_ns,
            "metadata": dict(self.metadata),
        }


class BaseIndex(ABC):
    """Abstract interface for key-value storage index implementations."""

    @abstractmethod
    def insert(self, key: Any, value: Any) -> None:
        """Insert a key-value record into the index."""
        pass

    @abstractmethod
    def search(self, key: Any) -> Optional[Any]:
        """Query value associated with key, returning None if absent."""
        pass

    @abstractmethod
    def __len__(self) -> int:
        """Return number of key-value pairs stored in the index."""
        pass
