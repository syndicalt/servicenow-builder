CREATE TABLE IF NOT EXISTS lifecycle_events (
    event_id TEXT PRIMARY KEY,
    event_type TEXT NOT NULL,
    story_number TEXT NOT NULL,
    payload_json JSONB NOT NULL,
    received_at TIMESTAMPTZ NOT NULL,
    validation_status TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS fulfillment_jobs (
    job_id TEXT PRIMARY KEY,
    event_id TEXT NOT NULL UNIQUE REFERENCES lifecycle_events(event_id),
    story_number TEXT NOT NULL,
    status TEXT NOT NULL,
    attempt_count INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL,
    locked_by TEXT,
    locked_at TIMESTAMPTZ,
    last_error TEXT
);

CREATE TABLE IF NOT EXISTS job_events (
    id BIGSERIAL PRIMARY KEY,
    job_id TEXT NOT NULL REFERENCES fulfillment_jobs(job_id),
    status TEXT NOT NULL,
    message TEXT,
    created_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS artifact_refs (
    id BIGSERIAL PRIMARY KEY,
    job_id TEXT NOT NULL REFERENCES fulfillment_jobs(job_id),
    artifact_kind TEXT NOT NULL,
    path TEXT NOT NULL,
    sha256 TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_fulfillment_jobs_status_created
    ON fulfillment_jobs(status, created_at, job_id);

CREATE INDEX IF NOT EXISTS idx_job_events_job_id
    ON job_events(job_id, id);

CREATE INDEX IF NOT EXISTS idx_artifact_refs_job_id
    ON artifact_refs(job_id, id);
