"""CyberSentry sentry_domain library."""
from libs.sentry_domain.models import Event, Detection, Incident
from libs.sentry_domain.severity import (
    SEVERITY_ORDER,
    SEVERITY_SCORE,
    CRITICALITY_MULTIPLIER,
    CorrelationError,
    SeverityError,
    severity_rank,
    max_severity,
    adjust_severity,
    risk_score,
)
from libs.sentry_domain.correlation import (
    Correlator,
    dedup_key,
    primary_entity,
)

__all__ = [
    "Event",
    "Detection",
    "Incident",
    "SEVERITY_ORDER",
    "SEVERITY_SCORE",
    "CRITICALITY_MULTIPLIER",
    "CorrelationError",
    "SeverityError",
    "severity_rank",
    "max_severity",
    "adjust_severity",
    "risk_score",
    "Correlator",
    "dedup_key",
    "primary_entity",
]
