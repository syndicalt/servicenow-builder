# Sprint 816 Change Log - Production outbound timeout ceiling validation

## Scope

Hardened production outbound timeout settings so alert delivery and public documentation retrieval
cannot be configured with multi-minute waits that stall worker responsiveness.

## Tests First

- Added 1 failing-first outbound timeout assertion:
  `tests/test_runtime.py::test_validate_runtime_settings_rejects_excessive_production_outbound_timeouts`.
- Added 1 failing-first sprint documentation assertion:
  `tests/test_project_docs.py::test_sprint_816_documents_production_outbound_timeout_ceilings`.
- Initial failure proved production worker validation accepted 300-second
  `JEDI_ALERT_WEBHOOK_TIMEOUT_SECONDS` and `JEDI_PUBLIC_WEB_TIMEOUT_SECONDS` values through direct
  `RuntimeSettings`.

## Changes

- `JEDI_ALERT_WEBHOOK_TIMEOUT_SECONDS` now has a production ceiling of `30`.
- `JEDI_PUBLIC_WEB_TIMEOUT_SECONDS` now has a production ceiling of `30`.
- Diagnostics name the setting and ceiling without echoing the oversized configured value.
- Updated the operator guide to document the outbound timeout ceilings.

## Verification

- `python3 -m pytest tests/test_runtime.py -q -k "excessive_production_outbound_timeouts or non_positive_runtime_limits"`: 2 passed, 366 deselected.
- `python3 -m pytest tests/test_project_docs.py -q -k sprint_816`: 1 passed, 888 deselected.
- `python3 -m pytest tests/test_runtime.py -q`: 368 passed.
- `python3 -m ruff check src tests`: all checks passed.
- `python3 -m mypy src tests`: success, no issues found in 199 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 3231 passed, 93.39% coverage.
