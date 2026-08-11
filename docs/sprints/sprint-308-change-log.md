# Sprint 308 Change Log - Split ServiceNow Blank Override Guard

## Summary

- Runtime settings loading now rejects blank split ServiceNow PM/DEV override values before legacy fallback resolution.
- `SERVICENOW_PM_INSTANCE_URL`, `SERVICENOW_PM_CLIENT_ID`, `SERVICENOW_PM_CLIENT_SECRET`, `SERVICENOW_DEV_INSTANCE_URL`, `SERVICENOW_DEV_CLIENT_ID`, and `SERVICENOW_DEV_CLIENT_SECRET` must be real values when present.
- Operators can still use the legacy single-instance fallback by omitting split keys entirely.
- Empty or whitespace-only split overrides cannot silently route PM story operations or DEV platform writes to the legacy fallback instance.
- Diagnostics name the blank split setting and do not echo fallback URLs or credential fragments.
- Existing split ServiceNow URL and OAuth credential validation remains intact after fallback resolution.
- Added failing regressions proving explicit blank split ServiceNow override env values were previously able to fall back to legacy ServiceNow settings.
- Documented the split ServiceNow blank-override boundary in the operator guide.

## Verification

- `python3 -m pytest tests/test_runtime.py -q -k "blank_split_servicenow_overrides or split_servicenow_oauth_credentials or split_servicenow_instance_urls or separates_pm_source"` - 3 tests failed before implementation because explicit blank split overrides could fall back to legacy ServiceNow settings.
- `python3 -m pytest tests/test_runtime.py -q -k "blank_split_servicenow_overrides or split_servicenow_oauth_credentials or split_servicenow_instance_urls or separates_pm_source"` - 13 passed after implementation.
- `python3 -m pytest tests/test_runtime.py -q` - 252 passed.
- `python3 -m pytest tests/test_project_docs.py::test_sprint_three_hundred_eight_documents_split_servicenow_blank_override_guard -q` - 1 passed.
- `python3 -m ruff check src/jedi_devproject/runtime_config.py tests/test_runtime.py tests/test_project_docs.py` - all checks passed.
- `python3 -m mypy src/jedi_devproject/runtime_config.py tests/test_runtime.py tests/test_project_docs.py` - no issues found in 3 source files.
- `python3 -m ruff check src tests` - all checks passed.
- `python3 -m mypy src tests` - no issues found in 179 source files.
- `python3 -m pytest tests/test_project_docs.py -q` - 382 passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 1840 passed, total coverage 93.88%.
