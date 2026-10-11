"""Incident domain models for network anomaly triage and alert queueing."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum, IntEnum
from typing import Any, Dict


class IncidentSeverity(IntEnum):
    """Urgency level where lower integer denotes higher priority for min-heap triage."""
    CRITICAL = 1      # Immediate service disruption / backbone failure
    HIGH = 2          # Regional degradation / redundant link down
    MEDIUM = 3        # High packet loss / latency threshold breach
    LOW = 4           # Minor sensor telemetry fluctuation
    INFORMATIONAL = 5 # Diagnostic or scheduled event notification


class IncidentType(str, Enum):
    """Topological failure categorization."""
    LINK_FAILURE = "LINK_FAILURE"
    HARDWARE_FAULT = "HARDWARE_FAULT"
    CONGESTION = "CONGESTION"
    POWER_OUTAGE = "POWER_OUTAGE"
    SECURITY_BREACH = "SECURITY_BREACH"
    SENSOR_ANOMALY = "SENSOR_ANOMALY"


@dataclass
class NetworkIncident:
    """Network alarm and operational incident record queued for triage.
    
    Attributes:
        id: Unique incident identifier (e.g. 'INC-00102').
        node_id: Originating network vertex ID.
        incident_type: Incident category.
        severity: Discrete urgency tier.
        priority_score: Numeric key for min-heap queueing (lower = higher priority).
        timestamp_ns: Nanosecond timestamp of alarm creation.
        description: Diagnostic alarm message.
        escalation_level: Number of times incident priority was escalated.
        is_resolved: Lifecycle status.
        metadata: Domain-specific telemetry diagnostics.
    """
    id: str
    node_id: str
    incident_type: IncidentType
    severity: IncidentSeverity = IncidentSeverity.MEDIUM
    priority_score: float = 3.0
    timestamp_ns: int = field(default_factory=time.time_ns)
    description: str = ""
    escalation_level: int = 0
    is_resolved: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("Incident id must be a non-empty string.")
        if not self.node_id:
            raise ValueError("Node id must be a non-empty string.")
        if self.priority_score <= 0.0:
            raise ValueError(f"Priority score must be strictly positive, got: {self.priority_score}")

    def escalate(self, score_reduction: float) -> None:
        """Escalate incident by decreasing priority score (making it more urgent in min-heap).
        
        Args:
            score_reduction: Positive decrement subtracted from priority_score.
        """
        if score_reduction <= 0.0:
            raise ValueError(f"Score reduction must be strictly positive, got: {score_reduction}")
        self.priority_score = max(0.1, self.priority_score - score_reduction)
        self.escalation_level += 1
        if self.priority_score < 1.5:
            self.severity = IncidentSeverity.CRITICAL
        elif self.priority_score < 2.5:
            self.severity = IncidentSeverity.HIGH

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "node_id": self.node_id,
            "incident_type": self.incident_type.value,
            "severity": self.severity.name,
            "priority_score": self.priority_score,
            "timestamp_ns": self.timestamp_ns,
            "description": self.description,
            "escalation_level": self.escalation_level,
            "is_resolved": self.is_resolved,
            "metadata": dict(self.metadata),
        }

