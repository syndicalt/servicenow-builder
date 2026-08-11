# Sprint 300 Change Log - ServiceNow Instance URL Settings Load Guard

## Summary

- Runtime settings loading now rejects malformed resolved split ServiceNow instance URLs before settings are returned.
- `SERVICENOW_PM_INSTANCE_URL` and `SERVICENOW_DEV_INSTANCE_URL` must be HTTPS ServiceNow targets without embedded credentials, fragments, raw or encoded whitespace, or control characters.
- The legacy single-instance fallback still works, but resolved PM/DEV URL values are validated after fallback expansion.
- Malformed URL diagnostics name only the resolved setting and do not echo URL credentials, fragments, or encoded control values.
- Existing direct `RuntimeSettings` production validation remains intact for non-env wiring.
- Added failing regressions proving non-HTTPS, credential-bearing, fragmented, and encoded-control split ServiceNow URLs were previously accepted during settings loading.
- Documented the ServiceNow instance URL settings-load boundary in the operator guide.

## Verification

- `python3 -m pytest tests/test_runtime.py -q -k "split_servicenow_instance_urls or separates_pm_source"` - 4 tests failed before implementation because malformed split ServiceNow instance URLs were accepted during settings loading.
- `python3 -m pytest tests/test_runtime.py -q -k "split_servicenow_instance_urls or separates_pm_source"` - 5 passed after implementation.
- `python3 -m pytest tests/test_runtime.py -q` - 230 passed.
- `python3 -m pytest tests/test_project_docs.py::test_sprint_three_hundred_documents_servicenow_instance_url_load_guard -q` - 1 passed.
- `python3 -m ruff check src/jedi_devproject/runtime_config.py tests/test_runtime.py tests/test_project_docs.py` - all checks passed.
- `python3 -m mypy src/jedi_devproject/runtime_config.py tests/test_runtime.py tests/test_project_docs.py` - no issues found in 3 source files.
- `python3 -m ruff check src tests` - all checks passed.
- `python3 -m mypy src tests` - no issues found in 179 source files.
- `python3 -m pytest tests/test_project_docs.py -q` - 374 passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 1807 passed, total coverage 93.90%.
