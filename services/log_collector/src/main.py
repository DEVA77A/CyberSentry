"""CyberSentry log-collector service."""
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="CyberSentry Log Collector", version="0.1.0-M1")


class TelemetryEnvelope(BaseModel):
    source_type: str = Field(..., description="Telemetry source, e.g. sysmon, zeek, cloudtrail")
    host_id: str | None = None
    payload: dict = Field(default_factory=dict)


@app.get("/health")
def health():
    return {"status": "ok", "service": "log-collector"}


@app.post("/ingest")
def ingest(event: TelemetryEnvelope):
    if not event.source_type:
        raise HTTPException(status_code=400, detail="source_type is required")
    # M1 scaffold: validates envelope and accepts ingestion
    return {"status": "accepted", "host_id": event.host_id}
