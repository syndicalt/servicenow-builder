# Sprint 813 Change Log - Production body-size ceiling validation

## Scope

Hardened production body-size configuration so ingress and alert-egress limits cannot be configured
so high that application memory becomes the real abuse-control boundary.

## Tests First

- Added 1 failing-first production body-size assertion:
  `tests/test_runtime.py::test_validate_runtime_settings_rejects_excessive_production_body_size_caps`.
- Added 1 failing-first sprint documentation assertion:
  `tests/test_project_docs.py::test_sprint_813_documents_production_body_size_ceilings`.
- Initial failure proved production validation accepted 10 MiB values for lifecycle webhook ingress,
  admin diagnostic ingress, and alert webhook egress body-size settings.

## Changes

- `JEDI_LIFECYCLE_WEBHOOK_MAX_BODY_BYTES` now has a production ceiling of `1048576`.
- `JEDI_ADMIN_MAX_BODY_BYTES` now has a production ceiling of `65536`.
- `JEDI_ALERT_WEBHOOK_MAX_BODY_BYTES` now has a production ceiling of `65536`.
- Diagnostics name the setting and ceiling without echoing the oversized configured value.
- Updated the operator guide to document the production body-size ceilings.

## Verification

- `python3 -m pytest tests/test_runtime.py -q -k "excessive_production_body_size_caps or non_positive_runtime_limits"`: 2 passed, 363 deselected.
- `python3 -m pytest tests/test_project_docs.py -q -k sprint_813`: 1 passed, 885 deselected.
- `python3 -m pytest tests/test_runtime.py -q`: 365 passed.
- `python3 -m ruff check src tests`: all checks passed.
- `python3 -m mypy src tests`: success, no issues found in 199 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 3225 passed, 93.38% coverage.
