# Sprint 109 Change Log

## Goal

Improve observability and audit correlation so an operator can follow work from a ServiceNow lifecycle event through fulfillment jobs, job events, artifact refs, admin views, and ServiceNow work notes.

## Changes

- Added `correlation_id` to lifecycle event and fulfillment job operational records.
- Derived fulfillment job correlation from the canonical lifecycle event payload instead of duplicating a mutable identifier into job rows.
- Returned `correlation_id` from admin JSON endpoints for lifecycle events and fulfillment jobs.
- Rendered `correlation_id` in the read-only admin console job and lifecycle event tables.
- Redacted diagnostic database URL passwords before returning admin job `last_error` values.
- Documented the audit correlation path in the operator guide.

## Tests

- Added operational-store tests for lifecycle-event and job correlation retrieval.
- Added admin JSON endpoint tests for correlation ids.
- Added admin console coverage proving the browser view renders the correlation id.
- Added admin diagnostic redaction coverage for database URL passwords.
- Added documentation tests for this sprint log and operator guide audit correlation guidance.

## Decision

The lifecycle payload remains the system of record for `correlation_id`. This avoids a schema-expanding trace table before it is needed, while still giving operators the trace path they need for the current MVP.
