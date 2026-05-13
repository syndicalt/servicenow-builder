# Sprint 68 Change Log

## Goal

Create a production-shaped local operational store before adding the webhook API and worker runtime.

## Changes

- Added `jedi_devproject.operational_store` with a SQLite-backed schema initializer.
- Added durable tables for `lifecycle_events`, `fulfillment_jobs`, `job_events`, and `artifact_refs`.
- Added idempotent lifecycle-event recording that preserves the original payload for duplicate `event_id` values.
- Added idempotent fulfillment-job enqueueing with one queued `job_events` entry per new job.
- Added `claim_next_fulfillment_job()` to claim queued work transactionally, increment attempt count, and record `locked_by` and `locked_at`.
- Added artifact reference recording so filesystem artifacts remain reviewable while operational state stays queryable.

## Verification

- Added tests for schema creation, lifecycle event idempotency, job enqueue idempotency, worker claiming, and artifact reference integrity.
- Added documentation tests for the README, operator guide, and this sprint log.

## Architecture Notes

SQLite is the MVP operational store. It is appropriate for the local runtime and the near-term containerized API plus worker topology. Generated packets, candidates, reports, and delivery evidence remain filesystem artifacts because reviewers need inspectable files and hashes.
