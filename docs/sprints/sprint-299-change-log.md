# Sprint 299 Change Log - ServiceNow OAuth Credential Settings Load Guard

## Summary

- Runtime settings loading now rejects malformed split ServiceNow OAuth credentials before settings are returned.
- `SERVICENOW_PM_CLIENT_ID`, `SERVICENOW_PM_CLIENT_SECRET`, `SERVICENOW_DEV_CLIENT_ID`, and `SERVICENOW_DEV_CLIENT_SECRET` must be unpadded and free of control characters.
- The legacy single-instance fallback still works, but resolved PM/DEV credential values are validated before the ServiceNow clients can be built.
- Malformed ServiceNow OAuth credential diagnostics name only the resolved setting and do not echo credential fragments.
- Existing direct `RuntimeSettings` production validation remains intact for non-env wiring.
- Added failing regressions proving padded and control-character split ServiceNow OAuth credential env values were previously accepted during settings loading.
- Documented the ServiceNow OAuth credential settings-load boundary in the operator guide.

## Verification

- `python3 -m pytest tests/test_runtime.py -q -k "split_servicenow_oauth_credentials or separates_pm_source"` - 4 tests failed before implementation because malformed split ServiceNow OAuth credentials were accepted during settings loading.
- `python3 -m pytest tests/test_runtime.py -q -k "split_servicenow_oauth_credentials or separates_pm_source"` - 5 passed after implementation.
- `python3 -m pytest tests/test_runtime.py -q` - 226 passed.
- `python3 -m pytest tests/test_project_docs.py::test_sprint_two_hundred_ninety_nine_documents_servicenow_oauth_load_guard -q` - 1 passed.
- `python3 -m ruff check src/jedi_devproject/runtime_config.py tests/test_runtime.py tests/test_project_docs.py` - all checks passed.
- `python3 -m mypy src/jedi_devproject/runtime_config.py tests/test_runtime.py tests/test_project_docs.py` - no issues found in 3 source files.
- `python3 -m ruff check src tests` - all checks passed.
- `python3 -m mypy src tests` - no issues found in 179 source files.
- `python3 -m pytest tests/test_project_docs.py -q` - 373 passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 1802 passed, total coverage 93.90%.
