from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class Event:
    event_id: str
    timestamp: datetime
    source_type: str
    host_id: str | None = None
    hostname: str | None = None
    user_name: str | None = None
    process_name: str | None = None
    process_guid: str | None = None
    parent_guid: str | None = None
    command_line: str | None = None
    source_ip: str | None = None
    destination_ip: str | None = None
    destination_port: int | None = None
    dns_query: str | None = None
    action: str | None = None
    outcome: str | None = None
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Detection:
    detection_id: str
    rule_code: str
    detected_at: datetime
    severity: str
    host_id: str | None = None
    user_name: str | None = None
    source_ip: str | None = None
    process_guid: str | None = None
    rule_version: int = 1
    risk_score: int = 0
    dedup_key: str | None = None
    evidence_index: str | None = None
    evidence_doc_id: str | None = None
    detail: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Incident:
    primary_entity: str
    entity_type: str
    detections: tuple[Detection, ...]
    severity: str
    risk_score: int
    window_start: datetime
    window_end: datetime
    incident_number: str | None = None
    status: str = "new"
