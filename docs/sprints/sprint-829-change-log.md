# Sprint 829 Change Log - Runtime request body limit construction guard

## Scope

Hardened runtime API construction so lifecycle webhook and admin request body limits cannot start with invalid values through direct `RuntimeSettings` paths.

## Tests First

- Added 1 failing-first runtime request body limit construction assertion: `tests/test_runtime.py::test_create_runtime_api_rejects_invalid_request_body_limits_before_store_open`.
- Added 1 failing-first sprint documentation assertion: `tests/test_project_docs.py::test_sprint_829_documents_runtime_request_body_limit_construction_guard`.
- Initial failure proved invalid lifecycle and admin body-size settings reached operational store construction before the runtime API rejected them.

## Changes

- Runtime API construction now rejects invalid `JEDI_LIFECYCLE_WEBHOOK_MAX_BODY_BYTES` and `JEDI_ADMIN_MAX_BODY_BYTES` values with `RuntimeConfigError`.
- The construction guard rejects non-positive values, non-integer values, and values above the production body-size ceilings.
- Request body limits are validated before lifecycle route creation, admin middleware use, operational store opening, or route serving.
- Updated the operator guide to document that runtime API construction rejects invalid request body limits in direct settings paths.

## Verification

- `python3 -m pytest tests/test_runtime.py -q -k "invalid_request_body_limits_before_store_open or admin_request_size"` - 7 passed, 392 deselected.
- `python3 -m pytest tests/test_project_docs.py -q -k sprint_829` - 1 passed, 901 deselected.
- `python3 -m pytest tests/test_runtime.py -q` - 399 passed.
- `python3 -m ruff check src tests` - All checks passed.
- `python3 -m mypy src tests` - Success: no issues found in 202 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 3280 passed, 93.37% coverage.
