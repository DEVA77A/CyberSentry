"""Severity, criticality and risk scoring logic for CyberSentry."""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from libs.sentry_domain.models import Detection

SEVERITY_ORDER: tuple[str, ...] = ("info", "low", "medium", "high", "critical")
SEVERITY_SCORE: dict[str, int] = {
    "info": 5,
    "low": 20,
    "medium": 45,
    "high": 70,
    "critical": 90,
}
CRITICALITY_MULTIPLIER: dict[str, float] = {
    "low": 0.8,
    "medium": 1.0,
    "high": 1.2,
    "crown_jewel": 1.5,
}


class CorrelationError(ValueError):
    """Raised when domain correlation, severity or scoring validation fails."""
    pass


SeverityError = CorrelationError


def severity_rank(severity: str) -> int:
    """Return numeric rank of severity string or raise CorrelationError."""
    if severity not in SEVERITY_ORDER:
        raise CorrelationError(f"unknown severity: {severity}")
    return SEVERITY_ORDER.index(severity)


def max_severity(severities: list[str]) -> str:
    """Return the highest severity among given list; raise if empty."""
    if not severities:
        raise CorrelationError("no severities supplied")
    return max(severities, key=severity_rank)


def adjust_severity(
    base: str,
    asset_criticality: str,
    is_internet_facing: bool = False,
) -> str:
    """Raise severity on important or exposed assets; never lower it below base."""
    rank = severity_rank(base)
    if asset_criticality == "crown_jewel":
        rank += 2
    elif asset_criticality == "high":
        rank += 1
    if is_internet_facing:
        rank += 1
    return SEVERITY_ORDER[min(rank, len(SEVERITY_ORDER) - 1)]


def risk_score(
    detections: list[Detection],
    asset_criticality: str = "medium",
) -> int:
    """Highest detection drives the score; additional distinct rules add corroboration.

    Summing severities would let a hundred low alerts outrank one LSASS dump,
    which is the wrong answer, so the base is the maximum, not the sum.
    """
    if not detections:
        raise CorrelationError("cannot score an empty incident")
    if asset_criticality not in CRITICALITY_MULTIPLIER:
        raise CorrelationError(f"unknown criticality: {asset_criticality}")

    base = max(SEVERITY_SCORE[d.severity] for d in detections)
    distinct_rules = len({d.rule_code for d in detections})
    corroboration = min(15, (distinct_rules - 1) * 5)
    score = (base + corroboration) * CRITICALITY_MULTIPLIER[asset_criticality]
    return int(min(100, round(score)))
