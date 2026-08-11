# Sprint 821 Change Log - Production admin API token ceiling validation

## Scope

Hardened production startup validation for configured admin bearer tokens so oversized tokens fail before API traffic reaches request-time auth.

## Tests First

- Added 1 failing-first production admin API token ceiling assertion: `tests/test_runtime.py::test_validate_runtime_settings_rejects_oversized_admin_api_token`.
- Added 1 failing-first sprint documentation assertion: `tests/test_project_docs.py::test_sprint_821_documents_production_admin_api_token_ceiling`.
- Initial failure proved production startup validation accepted a 8193-byte configured `JEDI_ADMIN_API_TOKEN`.

## Changes

- `JEDI_ADMIN_API_TOKEN` now has a production startup ceiling of 8192 bytes.
- Diagnostics name the setting and ceiling without echoing the oversized configured value.
- Updated the operator guide to document the production admin API token ceiling.

## Verification

- `python3 -m pytest tests/test_runtime.py -q -k "oversized_admin_api_token or weak_admin_api_token or admin_api_token_control_characters"` - 3 passed, 366 deselected.
- `python3 -m pytest tests/test_project_docs.py -q -k sprint_821` - 1 passed, 893 deselected.
- `python3 -m pytest tests/test_runtime.py -q` - 369 passed.
- `python3 -m ruff check src tests` - All checks passed.
- `python3 -m mypy src tests` - Success: no issues found in 199 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 3242 passed, 93.40% coverage.
