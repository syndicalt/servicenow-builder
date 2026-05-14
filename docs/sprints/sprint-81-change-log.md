# Sprint 81 Change Log

## Goal

Move implementation packet and implementation candidate artifacts from container-local JSON files into durable PostgreSQL JSON records.

## Changes

- Added an `artifact_blobs` table for DB-backed JSON artifacts with job id, story number, artifact kind, schema version, canonical SHA-256, and JSONB payload.
- Added `artifact_refs.artifact_id` so existing artifact references can point at durable DB artifacts through `db://artifact_blobs/<id>`.
- Added `record_json_artifact()` and `get_artifact_blob()` to the operational store.
- Extended fulfillment artifact results to carry JSON payloads and schema versions.
- Updated the fulfillment worker to persist JSON payload artifacts through the operational store before completing the job.
- Updated model candidate fulfillment so implementation packets and candidates are returned as DB-ready JSON payloads instead of filesystem files.
- Changed the ServiceNow work note for generated candidates to reference the fulfillment job id rather than ephemeral container paths.

## Verification

- Added schema and store tests for `artifact_blobs`, DB-backed refs, canonical JSON payload storage, and artifact retrieval.
- Added worker tests proving JSON artifacts are persisted through `record_json_artifact()`.
- Updated runtime OpenAI tests to assert implementation packet and candidate artifacts are DB-backed payloads.
- Ran focused tests for operational store, fulfillment worker, model fulfillment, and runtime OpenAI wiring.

## Architecture Notes

Implementation packets and implementation candidates are structured JSON and belong in PostgreSQL for the current runtime. This keeps Railway container files out of the audit path and gives the future admin GUI a typed DB read path. Larger delivery artifacts, such as reviewed Update Set XML or test evidence bundles, remain separate artifact types and should not be forced into this JSONB table by default.
