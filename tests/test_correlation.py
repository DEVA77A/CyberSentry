from datetime import datetime, timedelta, timezone
import pytest

from libs.sentry_domain.correlation import (
    Correlator,
    CorrelationError,
    Detection,
    dedup_key,
    primary_entity,
)

T0 = datetime(2026, 9, 11, 9, 0, tzinfo=timezone.utc)


def det(n, minutes=0, severity="medium", rule="DR001", host="HOST-0001", **kw):
    return Detection(
        detection_id=f"D{n}",
        rule_code=rule,
        detected_at=T0 + timedelta(minutes=minutes),
        severity=severity,
        host_id=host,
        **kw,
    )


def test_dedup_key_collapses_within_window():
    a = dedup_key("DR001", "HOST-1", T0, window_minutes=15)
    b = dedup_key("DR001", "HOST-1", T0 + timedelta(minutes=7), window_minutes=15)
    assert a == b


def test_dedup_key_separates_across_windows():
    a = dedup_key("DR001", "HOST-1", T0, window_minutes=15)
    b = dedup_key("DR001", "HOST-1", T0 + timedelta(minutes=40), window_minutes=15)
    assert a != b


def test_dedup_key_rejects_non_positive_window():
    with pytest.raises(CorrelationError):
        dedup_key("DR001", "HOST-1", T0, window_minutes=0)


def test_entity_precedence_prefers_host():
    d = Detection("D1", "DR001", T0, "low", host_id="H1", user_name="u1")
    assert primary_entity(d) == ("H1", "host")


def test_entity_precedence_prefers_identity_over_ip():
    d = Detection("D1", "DR001", T0, "low", user_name="u1", source_ip="192.168.1.1")
    assert primary_entity(d) == ("u1", "identity")


def test_entity_precedence_falls_back_to_ip():
    d = Detection("D1", "DR001", T0, "low", source_ip="10.0.0.1")
    assert primary_entity(d) == ("10.0.0.1", "source_ip")


def test_detection_without_entity_is_rejected():
    with pytest.raises(CorrelationError):
        primary_entity(Detection("D1", "DR001", T0, "low"))


def test_detections_within_window_form_one_incident():
    c = Correlator(window=timedelta(minutes=60))
    incidents = c.correlate([det(1, 0), det(2, 20), det(3, 45)])
    assert len(incidents) == 1
    assert len(incidents[0].detections) == 3


def test_a_gap_larger_than_the_window_splits_incidents():
    c = Correlator(window=timedelta(minutes=30))
    incidents = c.correlate([det(1, 0), det(2, 10), det(3, 200)])
    assert len(incidents) == 2


def test_different_entities_never_merge():
    c = Correlator()
    incidents = c.correlate([det(1, 0, host="HOST-A"), det(2, 5, host="HOST-B")])
    assert {i.primary_entity for i in incidents} == {"HOST-A", "HOST-B"}


def test_incidents_are_returned_highest_risk_first():
    c = Correlator(asset_criticality={"HOST-DC": "crown_jewel"})
    incidents = c.correlate([
        det(1, 0, severity="low", host="HOST-WS"),
        det(2, 0, severity="critical", host="HOST-DC"),
    ])
    assert incidents[0].primary_entity == "HOST-DC"


def test_zero_window_is_rejected():
    with pytest.raises(CorrelationError):
        Correlator(window=timedelta(0)).correlate([det(1)])
