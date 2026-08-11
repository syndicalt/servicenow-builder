# Sprint 835 Change Log - Admin result limit guard

## Intent

Harden admin diagnostic list endpoints so malformed non-positive result limits
fail before operational-store reads. Excessive positive limits remain capped to
the production diagnostic maximum.

## Changes

- Added 1 failing-first admin result limit assertion: `tests/test_runtime.py::test_admin_list_endpoints_reject_non_positive_limits_before_store_access`.
- Added 1 failing-first sprint documentation assertion: `tests/test_project_docs.py::test_sprint_835_documents_admin_result_limit_guard`.
- `GET /admin/lifecycle-events`, `GET /admin/jobs`, and `GET /admin/alerts` now reject non-positive `limit` values before store access.
- Positive limits above 100 remain capped to 100 for bounded diagnostic reads.

## Verification

- `pytest tests/test_runtime.py::test_admin_list_endpoints_reject_non_positive_limits_before_store_access tests/test_runtime.py::test_admin_lifecycle_events_caps_excessive_limits tests/test_runtime.py::test_admin_alerts_caps_excessive_limits tests/test_project_docs.py::test_sprint_835_documents_admin_result_limit_guard -q` - 9 passed.
- `pytest tests/test_runtime.py -q` - 405 passed.
- `pytest tests/test_project_docs.py -q` - 908 passed.
- `pytest --cov=src/jedi_devproject --cov-report=term-missing -q` - 3331 passed, 93.42% coverage.
