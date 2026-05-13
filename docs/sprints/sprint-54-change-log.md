# Sprint 54 Change Log

## Missing Artifact Preflight

- Added an `artifact_missing` preflight result for `attach-delivery-artifacts`.
- Made dry-run attachment planning fail closed when a reviewed delivery artifact path no longer exists.
- Replaced the raw missing-file traceback with a controlled CLI summary.
- Kept the missing-artifact check before ServiceNow client creation or attachment calls.
- Documented the missing artifact behavior alongside the existing hash mismatch gate.
