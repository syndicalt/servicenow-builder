# Sprint 69 Change Log

## Goal

Retarget operational state to PostgreSQL before the API server and worker runtime are built.

## Changes

- Replaced the SQLite-specific operational-store implementation with `PostgresOperationalStore`.
- Added `psycopg` as the PostgreSQL driver dependency.
- Added `db/migrations/0001_operational_store.sql` as the reviewed schema source for `lifecycle_events`, `fulfillment_jobs`, `job_events`, and `artifact_refs`.
- Stored lifecycle payloads as PostgreSQL `JSONB` and timestamps as `TIMESTAMPTZ`.
- Implemented worker claiming with `SELECT ... FOR UPDATE SKIP LOCKED` so multiple workers can claim queued jobs without blocking each other.
- Kept filesystem artifacts as reviewable files and stored only artifact references and hashes in PostgreSQL.

## Verification

- Replaced SQLite behavior tests with PostgreSQL contract tests for migrations, idempotent inserts, worker claims, and artifact references.
- Updated README and operator documentation to make PostgreSQL the required runtime store.

## Architecture Notes

PostgreSQL is now the required operational database for local runtime and future container deployment. SQLite is not retained as a compatibility backend because dual-store behavior would create false confidence and extra validation burden in a regulated delivery path.
