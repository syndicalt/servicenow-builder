# Sprint 100 Change Log

## Goal

Add a small operational visibility surface for the hosted runtime without moving the user work surface out of ServiceNow.

## Changes

- Added admin-only `GET /admin/lifecycle-events` for recent lifecycle event summaries.
- Added admin-only `GET /admin/jobs` for recent fulfillment job summaries.
- Added PostgreSQL store methods for bounded recent lifecycle event and fulfillment job reads.
- Kept lifecycle event payloads and ServiceNow sys_ids out of the summary response.
- Documented the admin summary endpoints in the operator guide.

## Verification

- `pytest tests/test_runtime.py::test_admin_lifecycle_events_lists_recent_events tests/test_runtime.py::test_admin_jobs_lists_recent_fulfillment_jobs tests/test_operational_store.py::test_recent_lifecycle_events_returns_newest_events tests/test_operational_store.py::test_recent_fulfillment_jobs_returns_newest_jobs -q`
- Full lint, type, and coverage gate before merge.

## Decision

Operational visibility belongs behind the existing admin bearer-token boundary and should expose minimal summaries first. Raw artifacts remain available through artifact-specific admin endpoints; lifecycle payloads stay in PostgreSQL for audit and are not returned by default list views.
