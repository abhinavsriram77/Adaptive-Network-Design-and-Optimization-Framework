"""Dispatch site domain models for technician field maintenance tours."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class DispatchSite:
    """Network location or maintenance depot requiring on-site field dispatch.
    
    Attributes:
        id: Unique site identifier (e.g., 'DEPOT-01' or 'SITE-HUB-A').
        name: Human-readable location description.
        latitude: Geographic coordinate [-90.0, 90.0].
        longitude: Geographic coordinate [-180.0, 180.0].
        service_time_mins: Estimated on-site maintenance duration in minutes.
        incident_id: Optional reference to an active NetworkIncident alarm.
        is_depot: True if this location serves as the dispatch starting/ending depot.
        metadata: Domain-specific technician or equipment requirements.
    """
    id: str
    name: str
    latitude: float = 0.0
    longitude: float = 0.0
    service_time_mins: float = 30.0
    incident_id: Optional[str] = None
    is_depot: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("DispatchSite id must be a non-empty string.")
        if not (-90.0 <= self.latitude <= 90.0):
            raise ValueError(f"Latitude must be within [-90.0, 90.0], got: {self.latitude}")
        if not (-180.0 <= self.longitude <= 180.0):
            raise ValueError(f"Longitude must be within [-180.0, 180.0], got: {self.longitude}")
        if self.service_time_mins < 0.0:
            raise ValueError(f"Service time must be non-negative, got: {self.service_time_mins}")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "service_time_mins": self.service_time_mins,
            "incident_id": self.incident_id,
            "is_depot": self.is_depot,
            "metadata": dict(self.metadata),
        }

