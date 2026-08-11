# Sprint 822 Change Log - Production admin API token ASCII validation

## Scope

Hardened production startup validation for configured admin bearer tokens so non-ASCII token values fail before API traffic reaches request-time auth.

## Tests First

- Added 1 failing-first production admin API token ASCII assertion: `tests/test_runtime.py::test_validate_runtime_settings_rejects_non_ascii_admin_api_token`.
- Added 1 failing-first sprint documentation assertion: `tests/test_project_docs.py::test_sprint_822_documents_production_admin_api_token_ascii_validation`.
- Initial failure proved production startup validation did not name non-ASCII configured `JEDI_ADMIN_API_TOKEN` values as invalid.

## Changes

- `JEDI_ADMIN_API_TOKEN` now requires ASCII-only values during production startup validation.
- Diagnostics name the setting and ASCII requirement without echoing the configured token.
- Updated the operator guide to document that non-ASCII configured bearer secrets fail before the API starts.

## Verification

- `python3 -m pytest tests/test_runtime.py -q -k "non_ascii_admin_api_token or oversized_admin_api_token or admin_api_token_control_characters"` - 3 passed, 367 deselected.
- `python3 -m pytest tests/test_project_docs.py -q -k "sprint_821 or sprint_822 or two_hundred_thirty_two_documents_admin_api_token_hygiene"` - 3 passed, 892 deselected.
- `python3 -m pytest tests/test_runtime.py -q` - 370 passed.
- `python3 -m ruff check src tests` - All checks passed.
- `python3 -m mypy src tests` - Success: no issues found in 199 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 3244 passed, 93.41% coverage.
