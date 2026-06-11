CREATE TABLE IF NOT EXISTS retention_prune_audit (
    id BIGSERIAL PRIMARY KEY,
    record_class TEXT NOT NULL,
    cutoff TIMESTAMPTZ NOT NULL,
    deleted_count BIGINT NOT NULL,
    batches INTEGER NOT NULL,
    pruned_at TIMESTAMPTZ NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_artifact_blobs_created_at
    ON artifact_blobs(created_at, id);

CREATE INDEX IF NOT EXISTS idx_job_events_created_at
    ON job_events(created_at, id);

-- Retention is disabled by default and must be enabled explicitly per
-- agency/customer retention rules. Pruning deletes only artifact_blobs and
-- job_events rows older than the configured window whose parent fulfillment
-- job is terminal (completed, failed, or rejected). Pruned artifact_blobs
-- keep their artifact_refs audit rows (path and sha256) with artifact_id
-- detached, and every prune run that deletes rows writes a
-- retention_prune_audit row so deletions remain auditable.
