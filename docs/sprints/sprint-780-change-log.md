# Sprint 780 Change Log - Compose split ServiceNow runtime values

## Scope

Hardened local compose ServiceNow wiring so API and worker services require split PM/DEV
credentials instead of exercising only the legacy single-instance fallback.

## Tests First

- Added 6 failing-first split ServiceNow compose assertions in `tests/test_container_runtime.py::test_compose_requires_split_servicenow_runtime_values`.
- Added 1 failing-first sprint documentation assertion: `tests/test_project_docs.py::test_sprint_780_documents_compose_split_servicenow_runtime_values`.
- Initial failures proved `docker-compose.yml` still passed `SERVICENOW_INSTANCE_URL`, `SERVICENOW_CLIENT_ID`, and `SERVICENOW_CLIENT_SECRET`, and this sprint log was absent.

## Changes

- Required `SERVICENOW_PM_INSTANCE_URL`, `SERVICENOW_PM_CLIENT_ID`, and `SERVICENOW_PM_CLIENT_SECRET` in compose API and worker services.
- Required `SERVICENOW_DEV_INSTANCE_URL`, `SERVICENOW_DEV_CLIENT_ID`, and `SERVICENOW_DEV_CLIENT_SECRET` in compose API and worker services.
- Removed legacy single-instance ServiceNow variables from compose service environments.
- Documented that legacy single-instance values remain direct-runtime fallback values, not compose service wiring.

## Verification

- `python3 -m pytest tests/test_container_runtime.py tests/test_project_docs.py -q -k "split_servicenow_runtime_values or sprint_780 or compose_defines_api_worker"`: 3 passed, 866 deselected.
- `python3 -m ruff check src tests`: All checks passed.
- `python3 -m mypy src tests`: Success, no issues found in 199 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 3151 passed, total coverage 93.36%.
