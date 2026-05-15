# Sprint 107 Change Log

## Goal

Harden the ServiceNow surface investigation layer so retrieved context is easier to trust, safer to display, and clearer when it blocks model generation.

## Changes

- Added per-surface confidence scores to `ServiceNowSurfaceContext`.
- Added per-surface citation records with source table, query, and retrieved record count.
- Added safe lookup by surface name for admin/debug consumers.
- Redacted script-like fields from surface metadata:
  - `script`
  - `condition`
  - `operation_script`
- Redacted URL query strings from integration endpoint summaries and metadata.
- Improved ServiceNow work notes for blocked model calls so missing context is named directly, for example `Missing ServiceNow context: flows`.

## Tests

- Added surface investigation coverage for confidence and citation metadata.
- Added redaction coverage proving scripts, query secrets, and sys_ids do not leak into the bundle JSON.
- Added work-note coverage proving missing ServiceNow context appears in story feedback.

## Decision

The admin console already exposes artifact JSON, including `instance_context_bundle`, so the immediate hardening value is higher-quality artifact content rather than another UI surface. This sprint improves evidence quality and display safety while preserving the read-only admin posture.
