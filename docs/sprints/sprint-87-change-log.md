# Sprint 87 Change Log

## Goal

Add a non-destructive ServiceNow CI/CD Update Set API capability probe before changing fulfillment architecture.

## Changes

- Added `evaluate_cicd_update_set_capability()` for read-only CI/CD Update Set API endpoint checks.
- Added `ServiceNowClient.probe_cicd_update_set_endpoint()` for `create` and `retrieve` probes.
- Added `check-cicd-update-set-capability` to the CLI.
- Kept generated fulfillment handoff unchanged while the CI/CD API behavior is verified.

## Tests

- Added coverage for successful `400` missing-parameter probes on `create` and `retrieve`.
- Added coverage for fail-closed `403` probe responses.
- Added ServiceNow transport coverage proving the probe sends no mutation body.
- Added CLI coverage for capability reporting without leaking credentials.

## Decision

The CI/CD Update Set API should be treated as a lifecycle API, not assumed to be a raw XML import API. This sprint only proves endpoint availability. Promotion architecture still needs either a ServiceNow update source/build instance or a reviewed ServiceNow-side importer before generated candidates can become previewable and committable update sets.
