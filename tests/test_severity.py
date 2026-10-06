from datetime import datetime, timezone
import pytest

from libs.sentry_domain.models import Detection
from libs.sentry_domain.severity import (
    CorrelationError,
    adjust_severity,
    max_severity,
    risk_score,
    severity_rank,
)

T0 = datetime(2026, 9, 11, 9, 0, tzinfo=timezone.utc)


def det(n: int = 1, severity: str = "medium", rule: str = "DR001") -> Detection:
    return Detection(
        detection_id=f"D{n}",
        rule_code=rule,
        detected_at=T0,
        severity=severity,
        host_id="HOST-0001",
    )


def test_severity_ranking_order():
    assert severity_rank("info") < severity_rank("low") < severity_rank("medium") < severity_rank("high") < severity_rank("critical")


def test_unknown_severity_rank_raises():
    with pytest.raises(CorrelationError):
        severity_rank("catastrophic")


def test_max_severity_picks_the_worst():
    assert max_severity(["low", "critical", "medium"]) == "critical"


def test_max_severity_rejects_empty():
    with pytest.raises(CorrelationError):
        max_severity([])


def test_crown_jewel_raises_severity():
    assert adjust_severity("medium", "crown_jewel") == "critical"


def test_severity_never_exceeds_critical():
    assert adjust_severity("critical", "crown_jewel", True) == "critical"


def test_severity_is_never_lowered():
    assert adjust_severity("high", "low") == "high"


def test_internet_facing_bumps_severity():
    assert adjust_severity("low", "medium", is_internet_facing=True) == "medium"


def test_risk_uses_max_not_sum():
    many_low = [det(i, severity="low") for i in range(30)]
    one_critical = [det(99, severity="critical")]
    assert risk_score(one_critical) > risk_score(many_low)


def test_distinct_rules_add_corroboration():
    single = [det(1, severity="high")]
    corroborated = [det(1, severity="high"), det(2, severity="high", rule="DR004")]
    assert risk_score(corroborated) > risk_score(single)


def test_corroboration_is_capped():
    many = [det(i, severity="high", rule=f"DR{i:03d}") for i in range(20)]
    assert risk_score(many) <= 100


def test_risk_rejects_empty_incident():
    with pytest.raises(CorrelationError):
        risk_score([])


def test_risk_rejects_unknown_criticality():
    with pytest.raises(CorrelationError):
        risk_score([det(1)], asset_criticality="unknown_level")
