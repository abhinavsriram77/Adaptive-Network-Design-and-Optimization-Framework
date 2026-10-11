"""Abstract base contracts and metrics for priority queue triage implementations."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Optional, Tuple


@dataclass
class QueueTelemetry:
    """Operational telemetry counters for priority queue operations."""
    inserts: int = 0
    extract_mins: int = 0
    find_mins: int = 0
    decrease_keys: int = 0
    unions: int = 0
    comparisons: int = 0

    def reset(self) -> None:
        self.inserts = 0
        self.extract_mins = 0
        self.find_mins = 0
        self.decrease_keys = 0
        self.unions = 0
        self.comparisons = 0

    @property
    def total_operations(self) -> int:
        return self.inserts + self.extract_mins + self.find_mins + self.decrease_keys + self.unions

    @property
    def escalation_ratio(self) -> float:
        """Ratio of decrease_key operations to total modifications (inserts + decrease_keys)."""
        mods = self.inserts + self.decrease_keys
        if mods == 0:
            return 0.0
        return self.decrease_keys / mods


class BasePriorityQueue(ABC):
    """Abstract interface for advanced priority queues (Binomial & Fibonacci Heaps)."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Descriptive algorithm designation."""
        pass

    @abstractmethod
    def insert(self, key: float, value: Any) -> Any:
        """Insert a key-value pair and return an opaque node reference for decrease_key."""
        pass

    @abstractmethod
    def find_min(self) -> Optional[Tuple[float, Any]]:
        """Return (min_key, min_value) without removing, or None if queue is empty."""
        pass

    @abstractmethod
    def extract_min(self) -> Optional[Tuple[float, Any]]:
        """Remove and return (min_key, min_value), or None if queue is empty."""
        pass

    @abstractmethod
    def decrease_key(self, node: Any, new_key: float) -> None:
        """Lower the key of an existing node in the queue."""
        pass

    @abstractmethod
    def union(self, other: BasePriorityQueue) -> None:
        """Merge all elements of other into self (other becomes empty)."""
        pass

    @abstractmethod
    def __len__(self) -> int:
        """Total elements currently in the priority queue."""
        pass

    def is_empty(self) -> bool:
        """Whether queue contains zero elements."""
        return len(self) == 0

