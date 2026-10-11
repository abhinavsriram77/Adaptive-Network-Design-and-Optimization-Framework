"""Adaptive Priority Queue Triage Selector for network incident prioritization.

Dynamically selects and orchestrates between Binomial Heap (deterministic low overhead)
and Fibonacci Heap (amortized O(1) dynamic escalation) based on workload metrics.
"""

from __future__ import annotations

import time
from typing import Any, Dict, Optional, Tuple

from prioritization.base import BasePriorityQueue
from prioritization.binomial_heap import BinomialHeap
from prioritization.fibonacci_heap import FibonacciHeap
from prioritization.incident import NetworkIncident


class AdaptiveTriageSelector:
    """Orchestrates incident triage priority queues based on dynamic alarm workload.
    
    Attributes:
        escalation_threshold: Ratio of decrease_key operations to total modifications
                             triggering migration to Fibonacci Heap (default: 0.20).
    """

    def __init__(
        self,
        escalation_threshold: float = 0.20,
        initial_queue_type: str = "binomial",
    ) -> None:
        self.escalation_threshold = escalation_threshold
        self.queue: BasePriorityQueue = (
            BinomialHeap() if initial_queue_type == "binomial" else FibonacciHeap()
        )
        self._incident_index: Dict[str, Tuple[Any, NetworkIncident]] = {}

        self.total_ingested = 0
        self.total_dispatched = 0
        self.total_escalations = 0

    @property
    def current_algorithm(self) -> str:
        return self.queue.name

    def ingest_incident(self, incident: NetworkIncident) -> None:
        """Ingest a new network incident alarm into the priority triage queue."""
        if incident.id in self._incident_index:
            raise ValueError(f"Incident {incident.id!r} is already active in triage.")

        node_ref = self.queue.insert(incident.priority_score, incident)
        self._incident_index[incident.id] = (node_ref, incident)
        self.total_ingested += 1

        self._evaluate_workload_and_adapt()

    def escalate_incident(self, incident_id: str, score_reduction: float) -> NetworkIncident:
        """Escalate an active incident by decreasing its priority score (higher urgency).
        
        Args:
            incident_id: Active incident ID.
            score_reduction: Amount to reduce priority score by.
            
        Returns:
            Updated NetworkIncident.
        """
        if incident_id not in self._incident_index:
            raise KeyError(f"Incident {incident_id!r} not found in active triage queue.")

        node_ref, incident = self._incident_index[incident_id]
        incident.escalate(score_reduction)
        self.queue.decrease_key(node_ref, incident.priority_score)

        self.total_escalations += 1
        self._evaluate_workload_and_adapt()

        return incident

    def dispatch_highest_priority(self) -> Optional[NetworkIncident]:
        """Extract and return the most urgent network incident for worker remediation."""
        extracted = self.queue.extract_min()
        if extracted is None:
            return None

        _, incident = extracted
        if incident.id in self._incident_index:
            del self._incident_index[incident.id]

        self.total_dispatched += 1
        return incident

    def peek_highest_priority(self) -> Optional[NetworkIncident]:
        """Inspect the most urgent incident without removing it."""
        min_entry = self.queue.find_min()
        if min_entry is None:
            return None
        return min_entry[1]

    def merge_regional_queue(self, other_selector: AdaptiveTriageSelector) -> None:
        """Merge another regional selector's queue into self."""
        # For multi-queue coalescing, ensure we are using FibonacciHeap for O(1) union
        if not isinstance(self.queue, FibonacciHeap):
            self._migrate_to_fibonacci()

        # If other is Binomial, migrate it first to Fibonacci for uniform union
        if not isinstance(other_selector.queue, FibonacciHeap):
            other_selector._migrate_to_fibonacci()

        self.queue.union(other_selector.queue)
        self._incident_index.update(other_selector._incident_index)
        self.total_ingested += other_selector.total_ingested
        self.total_escalations += other_selector.total_escalations
        other_selector._incident_index.clear()

    def _evaluate_workload_and_adapt(self) -> None:
        """Check if dynamic escalation frequency warrants transitioning to Fibonacci Heap."""
        total_mods = self.total_ingested + self.total_escalations
        if total_mods < 10:
            return

        escalation_ratio = self.total_escalations / total_mods
        if escalation_ratio >= self.escalation_threshold and isinstance(self.queue, BinomialHeap):
            self._migrate_to_fibonacci()

    def _migrate_to_fibonacci(self) -> None:
        """Dynamically migrate existing items to a Fibonacci Heap."""
        new_fib = FibonacciHeap()
        new_index: Dict[str, Tuple[Any, NetworkIncident]] = {}

        for inc_id, (_, inc) in self._incident_index.items():
            new_node = new_fib.insert(inc.priority_score, inc)
            new_index[inc_id] = (new_node, inc)

        self.queue = new_fib
        self._incident_index = new_index

    def get_triage_metrics(self) -> Dict[str, Any]:
        """Telemetry diagnostics of triage operations."""
        total_mods = self.total_ingested + self.total_escalations
        escalation_ratio = self.total_escalations / total_mods if total_mods > 0 else 0.0

        return {
            "active_incidents": len(self.queue),
            "total_ingested": self.total_ingested,
            "total_dispatched": self.total_dispatched,
            "total_escalations": self.total_escalations,
            "escalation_ratio": escalation_ratio,
            "selected_algorithm": self.current_algorithm,
            "escalation_threshold": self.escalation_threshold,
            "raw_queue_telemetry": {
                "inserts": self.queue.telemetry.inserts,
                "extract_mins": self.queue.telemetry.extract_mins,
                "decrease_keys": self.queue.telemetry.decrease_keys,
                "unions": self.queue.telemetry.unions,
                "comparisons": self.queue.telemetry.comparisons,
            },
        }

