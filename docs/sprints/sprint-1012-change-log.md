# Sprint 1012 Change Log - Operational store read-row collection guard

## Summary

Hardened operational-store list read paths so database row collections are validated before API, admin, or worker read models consume them.

## Security

`requeue_stale_running_jobs()`, `job_events_for_job()`, `recent_lifecycle_events()`, `recent_fulfillment_jobs()`, and `artifact_refs_for_job()` now route `fetch_all()` results through `_operational_read_rows()`.

The helper accepts only exact Python lists containing exact Python dictionaries and fails closed with `operational store read rows contain non-JSON value`.

Malformed operational-store read collections fail before collection iteration, row subclass hooks, Pydantic model validation, admin timeline rendering, stale-job requeue reporting, artifact reference rendering, API JSON serialization, or worker decision reporting can consume caller-controlled database row behavior.

## Tests

- Added 1 failing-first operational-store read-row collection subclass assertion: `test_recent_lifecycle_events_rejects_row_collection_subclass_without_leak`.
- Added 1 failing-first operational-store read-row subclass assertion: `test_recent_lifecycle_events_rejects_row_subclass_without_leak`.
- Added 1 documentation assertion: `test_sprint_1012_documents_operational_store_read_row_collection_guard`.

## Verification

- `pytest tests/test_operational_store.py::test_recent_lifecycle_events_rejects_row_collection_subclass_without_leak tests/test_operational_store.py::test_recent_lifecycle_events_rejects_row_subclass_without_leak -q` failed before implementation because unsafe collection iteration executed and row subclasses were accepted into model validation.
- `pytest tests/test_operational_store.py::test_recent_lifecycle_events_rejects_row_collection_subclass_without_leak tests/test_operational_store.py::test_recent_lifecycle_events_rejects_row_subclass_without_leak tests/test_operational_store.py::test_recent_lifecycle_events_returns_newest_events tests/test_operational_store.py::test_recent_fulfillment_jobs_returns_newest_jobs tests/test_operational_store.py::test_artifact_refs_include_artifact_id_when_present -q` - 5 passed.
