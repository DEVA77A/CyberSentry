"""Pure severity and correlation logic.

Nothing here reads a database or a broker. Correlation is deterministic on
purpose: an analyst must be able to reproduce why these detections became one
incident, months later, during a post-incident review.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta

from libs.sentry_domain.models import Detection, Incident
from libs.sentry_domain.severity import (
    CRITICALITY_MULTIPLIER,
    SEVERITY_ORDER,
    SEVERITY_SCORE,
    CorrelationError,
    SeverityError,
    adjust_severity,
    max_severity,
    risk_score,
    severity_rank,
)


def dedup_key(
    rule_code: str,
    entity: str,
    detected_at: datetime,
    window_minutes: int = 15,
) -> str:
    """Stable across replays: the same rule and entity inside one window collapse."""
    if window_minutes <= 0:
        raise CorrelationError("dedup window must be positive")
    epoch_minutes = int(detected_at.timestamp() // 60)
    bucket = epoch_minutes // window_minutes
    return f"{rule_code}|{entity}|{bucket}"


def primary_entity(detection: Detection) -> tuple[str, str]:
    """Entity precedence: host, then identity, then source address."""
    if detection.host_id:
        return detection.host_id, "host"
    if detection.user_name:
        return detection.user_name, "identity"
    if detection.source_ip:
        return detection.source_ip, "source_ip"
    raise CorrelationError(f"detection {detection.detection_id} has no correlatable entity")


@dataclass
class Correlator:
    window: timedelta = field(default_factory=lambda: timedelta(minutes=60))
    asset_criticality: dict = field(default_factory=dict)

    def correlate(self, detections: list[Detection]) -> list[Incident]:
        """Group by entity, then split each group on gaps larger than the window."""
        if self.window <= timedelta(0):
            raise CorrelationError("correlation window must be positive")

        buckets: dict[tuple[str, str], list[Detection]] = {}
        for d in detections:
            key = primary_entity(d)
            buckets.setdefault(key, []).append(d)

        incidents: list[Incident] = []
        for (entity, entity_type), group in buckets.items():
            group.sort(key=lambda d: d.detected_at)
            chain: list[Detection] = [group[0]]
            for previous, current in zip(group, group[1:]):
                if current.detected_at - previous.detected_at <= self.window:
                    chain.append(current)
                else:
                    incidents.append(self._build(entity, entity_type, chain))
                    chain = [current]
            incidents.append(self._build(entity, entity_type, chain))

        incidents.sort(key=lambda i: (-i.risk_score, i.window_start))
        return incidents

    def _build(self, entity: str, entity_type: str, chain: list[Detection]) -> Incident:
        criticality = self.asset_criticality.get(entity, "medium")
        return Incident(
            primary_entity=entity,
            entity_type=entity_type,
            detections=tuple(chain),
            severity=adjust_severity(max_severity([d.severity for d in chain]), criticality),
            risk_score=risk_score(chain, criticality),
            window_start=chain[0].detected_at,
            window_end=chain[-1].detected_at,
        )


__all__ = [
    "CRITICALITY_MULTIPLIER",
    "CorrelationError",
    "Correlator",
    "Detection",
    "Incident",
    "SEVERITY_ORDER",
    "SEVERITY_SCORE",
    "SeverityError",
    "adjust_severity",
    "dedup_key",
    "max_severity",
    "primary_entity",
    "risk_score",
    "severity_rank",
]
