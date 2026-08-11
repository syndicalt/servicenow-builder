# Sprint 830 Change Log - Lifecycle API body limit factory guard

## Scope

Hardened the lower-level lifecycle API factory so direct lifecycle app wiring cannot start with an invalid request body limit.

## Tests First

- Added 1 failing-first lifecycle API body limit construction assertion: `tests/test_lifecycle_api.py::test_lifecycle_api_rejects_invalid_body_limit_at_construction`.
- Added 1 failing-first sprint documentation assertion: `tests/test_project_docs.py::test_sprint_830_documents_lifecycle_api_body_limit_factory_guard`.
- Initial failure proved `create_lifecycle_api()` accepted zero, negative, boolean, and string body limits at construction and deferred failure until request body reading.

## Changes

- `create_lifecycle_api()` now validates `max_request_body_bytes` before FastAPI app construction.
- Invalid direct body limits fail with `ValueError` using the stable diagnostic `max_request_body_bytes must be a positive integer`.
- The runtime wrapper remains responsible for environment-backed production ceilings such as `JEDI_LIFECYCLE_WEBHOOK_MAX_BODY_BYTES<=1048576`.
- Updated the operator guide to document the lifecycle API factory contract.

## Verification

- `python3 -m pytest tests/test_lifecycle_api.py -q -k "invalid_body_limit_at_construction or oversized_payload"` - 5 passed, 45 deselected.
- `python3 -m pytest tests/test_project_docs.py -q -k sprint_830` - 1 passed, 902 deselected.
- `python3 -m pytest tests/test_lifecycle_api.py -q` - 50 passed.
- `python3 -m pytest tests/test_runtime.py -q` - 399 passed.
- `python3 -m ruff check src tests` - All checks passed.
- `python3 -m mypy src tests` - Success: no issues found in 202 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 3285 passed, 93.38% coverage.
