# Sprint 82 Change Log

## Goal

Expose DB-backed implementation artifacts through a guarded runtime API for the future admin GUI and operator diagnostics.

## Changes

- Added optional `JEDI_ADMIN_API_TOKEN` runtime configuration.
- Added `GET /artifacts/{artifact_id}` to return artifact metadata and JSON payloads from `artifact_blobs`.
- Added `GET /jobs/{job_id}/artifacts` to list DB-backed artifact references for one fulfillment job.
- Required `Authorization: Bearer <JEDI_ADMIN_API_TOKEN>` for artifact reads.
- Kept ServiceNow lifecycle webhook calls separate from artifact admin API authentication.
- Documented the artifact retrieval endpoints in the operator guide.

## Verification

- Added API tests for missing token, wrong token, successful artifact reads, missing artifact `404`, and job-specific artifact listing.
- Added runtime settings coverage for `JEDI_ADMIN_API_TOKEN`.
- Updated runtime store fakes to include typed artifact read methods.

## Architecture Notes

The public lifecycle webhook remains narrow: receive, validate, persist, enqueue. Artifact inspection is a separate admin surface guarded by a server-side bearer token. This is sufficient for development and Railway testing; production should replace or wrap it with the customer-approved identity layer before exposing an admin GUI in a regulated environment.
