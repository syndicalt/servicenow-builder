# Sprint 833 Change Log - Retention prune direct-policy guard

## Intent

Harden the direct retention pruning primitive so embedded callers cannot bypass
environment parsing, open the operational store, and then fail late with a
malformed retention policy.

## Changes

- Added 1 failing-first retention prune policy assertion: `tests/test_runtime_worker_retention.py::test_prune_operational_store_rejects_invalid_policy_before_store_open`.
- Added 1 failing-first sprint documentation assertion: `tests/test_project_docs.py::test_sprint_833_documents_retention_prune_direct_policy_guard`.
- `prune_operational_store()` now validates direct `RetentionPolicy` instances before store acquisition.
- Invalid direct `JEDI_RETENTION_ARTIFACT_BLOB_DAYS` and `JEDI_RETENTION_JOB_EVENT_DAYS` shaped values fail before PostgreSQL access.
- Invalid direct `JEDI_RETENTION_PRUNE_BATCH_SIZE` shaped values, including values over 5000, fail before PostgreSQL access.

## Verification

- `pytest tests/test_runtime_worker_retention.py::test_prune_operational_store_rejects_invalid_policy_before_store_open tests/test_runtime_worker_retention.py::test_prune_operational_store_uses_store_factory_and_prints_report tests/test_project_docs.py::test_sprint_833_documents_retention_prune_direct_policy_guard -q` - 12 passed.
- `pytest tests/test_runtime_worker_retention.py -q` - 71 passed.
- `pytest tests/test_project_docs.py -q` - 906 passed.
- `pytest --cov=src/jedi_devproject --cov-report=term-missing -q` - 3319 passed, 93.40% coverage.
