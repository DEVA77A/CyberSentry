-- M2: one generic prediction table, shared by every model this project trains.
-- The M1 nullable columns are filled FROM this table (step 2.11), so the raw
-- predictions stay auditable even if the M1 join keys change later.
CREATE TABLE IF NOT EXISTS ml_predictions (
    entity_id TEXT NOT NULL,
    step TEXT NOT NULL, -- cycle, timestamp, date or token span
    model_name TEXT NOT NULL,
    model_version TEXT NOT NULL, -- registry name:version, e.g. my-model:v3
    score DOUBLE PRECISION,
    label TEXT,
    extra JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (entity_id, step, model_name)
);
CREATE INDEX IF NOT EXISTS ix_ml_predictions_model ON ml_predictions (model_name, model_version);

-- M1 auth_events store and alerts table
CREATE TABLE IF NOT EXISTS auth_events (
    event_ref TEXT PRIMARY KEY,
    step INT,
    src_user TEXT,
    src_comp TEXT,
    dst_comp TEXT,
    auth_type TEXT,
    outcome TEXT,
    risk_score DOUBLE PRECISION,
    model_version TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_auth_events_risk_score ON auth_events (risk_score);

CREATE TABLE IF NOT EXISTS alerts (
    id BIGSERIAL PRIMARY KEY,
    event_ref TEXT NOT NULL,
    layer TEXT NOT NULL,
    score DOUBLE PRECISION NOT NULL,
    techniques TEXT[] NOT NULL DEFAULT '{}',
    evidence JSONB NOT NULL DEFAULT '{}'::jsonb,
    model_version TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_alerts_event_ref ON alerts (event_ref);
