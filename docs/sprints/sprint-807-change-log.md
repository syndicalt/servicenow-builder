# Sprint 807 Change Log - Direct fulfillment API-role boundary

## Scope

Hardened the direct worker-side fulfillment facade so API-configured runtimes cannot claim or
fulfill queued work through library calls or external schedulers.

## Tests First

- Added 1 failing-first direct fulfillment role assertion:
  `tests/test_runtime.py::test_process_one_runtime_fulfillment_rejects_api_role_before_servicenow_or_store`.
- Added 1 failing-first sprint documentation assertion:
  `tests/test_project_docs.py::test_sprint_807_documents_direct_fulfillment_role_boundary`.
- Initial failure proved `process_one_runtime_fulfillment()` reached the store factory while
  `JEDI_RUNTIME_ROLE=api` was active.

## Changes

- `process_one_runtime_fulfillment()` now rejects `JEDI_RUNTIME_ROLE=api` before runtime validation,
  ServiceNow client creation, operational store access, or queued-work claiming.
- The API role remains limited to public HTTP surfaces.
- Fulfillment execution remains owned by `JEDI_RUNTIME_ROLE=worker` or explicitly accepted local
  `combined` runtimes.
- Updated the operator guide to call out the direct fulfillment boundary for external schedulers.

## Verification

- `python3 -m pytest tests/test_runtime.py -q -k "process_one_runtime_fulfillment_rejects_api_role_before_servicenow_or_store or process_one_runtime_fulfillment_validates_production_settings_before_store_open"`: 2 passed, 352 deselected.
- `python3 -m pytest tests/test_project_docs.py -q -k sprint_807`: 1 passed, 879 deselected.
- `python3 -m pytest tests/test_runtime.py -q`: 354 passed.
- `python3 -m ruff check src tests`: all checks passed.
- `python3 -m mypy src tests`: success, no issues found in 199 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 3208 passed, 93.37% coverage.
