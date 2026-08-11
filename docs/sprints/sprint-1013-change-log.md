# Sprint 1013 Change Log - Operational store single-row read guard

## Summary
Hardened operational-store single-row read paths so database rows are validated before API, admin, or worker read models consume or index them.

## Security
`get_lifecycle_event()`, `enqueue_fulfillment_job()`, `claim_next_fulfillment_job()`, `get_job()`, fulfillment job transition readers, artifact reference creation, artifact blob creation and lookup, and retention prune count reads now route returned `fetch_one()` rows through `_operational_read_row()` after normal missing-row handling.

The helper accepts only exact Python dictionaries and fails closed with `operational store read row contains non-JSON value`.

Malformed operational-store single-row results fail before row indexing, Pydantic model validation, artifact id extraction, retention count conversion, admin detail rendering, worker status reporting, or API JSON serialization can consume caller-controlled database row behavior.

## Tests
- Added 1 failing-first operational-store single-row subclass assertion: `test_enqueue_fulfillment_job_rejects_row_subclass_without_leak`.
- Added 1 failing-first artifact blob row subclass assertion: `test_record_json_artifact_rejects_blob_row_subclass_before_indexing_without_leak`.
- Added 1 documentation assertion: `test_sprint_1013_documents_operational_store_single_read_row_guard`.

## Verification
- `pytest tests/test_operational_store.py::test_enqueue_fulfillment_job_rejects_row_subclass_without_leak tests/test_operational_store.py::test_record_json_artifact_rejects_blob_row_subclass_before_indexing_without_leak -q` failed before implementation because single-row subclasses reached Pydantic or row indexing.
