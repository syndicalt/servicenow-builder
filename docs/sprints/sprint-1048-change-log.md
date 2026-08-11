# Sprint 1048 Change Log - Maintenance database URL boundary

## Summary

Sprint 1048 continued production hardening by tightening direct maintenance database URL validation. `prune_operational_store()` and `requeue_stale_running_jobs()` already validated their retention and stale-recovery controls before store acquisition, but embedded callers could still pass direct `RuntimeSettings.database_url` values to maintenance store factories without the shared exact-string and PostgreSQL URL hygiene boundary.

## Security

- `prune_operational_store()` now validates `RuntimeSettings.database_url` before opening the pruning store.
- `requeue_stale_running_jobs()` now validates `RuntimeSettings.database_url` before opening the stale-job recovery store.
- Maintenance database URLs use the same exact-string and PostgreSQL URL hygiene checks as production startup.
- String subclasses, non-PostgreSQL URLs, whitespace/control-character URLs, encoded-control URLs, and fragmented URLs fail before store acquisition, PostgreSQL mutation, job-event audit insertion, or runtime report output.

## Tests

- Added 4 failing-first maintenance database URL assertions:
  `test_prune_operational_store_rejects_database_url_string_subclass_before_store_open`,
  `test_prune_operational_store_rejects_malformed_database_url_before_store_open`,
  `test_requeue_stale_running_jobs_rejects_database_url_string_subclass_before_store_open`, and
  `test_requeue_stale_running_jobs_rejects_malformed_database_url_before_store_open`.
- Re-ran focused successful pruning and stale recovery store-factory tests after implementation.
- Added documentation coverage: `test_sprint_1048_documents_maintenance_database_url_boundary`.

## Verification

- Focused tests failed before implementation because direct maintenance functions reached store factories with malformed database URLs.
- Focused maintenance boundary and successful store-factory tests passed after implementation.
