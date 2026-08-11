# Sprint 297 Change Log - Admin API Token Settings Load Guard

## Summary

- Runtime settings loading now rejects malformed admin API bearer-token configuration.
- `JEDI_ADMIN_API_TOKEN` must be unpadded and free of control characters before runtime settings are returned.
- Blank or absent admin API token values still behave as unconfigured, preserving the fail-closed admin artifact API path.
- Malformed admin API token diagnostics name only the setting and do not echo token fragments.
- Existing production validation still enforces the minimum 32-character admin API token strength requirement.
- Added failing regressions proving padded and control-character admin API token env values were previously accepted during settings loading.
- Documented the admin API token settings-load boundary in the operator guide.

## Verification

- `python3 -m pytest tests/test_runtime.py -q -k "admin_api_token and load_runtime_settings"` - 3 tests failed before implementation because malformed admin API token values were accepted during settings loading.
- `python3 -m pytest tests/test_runtime.py -q -k "admin_api_token and load_runtime_settings"` - 4 passed after implementation.
- `python3 -m pytest tests/test_runtime.py -q -k "admin_api_token or admin_token or bearer"` - 11 passed.
- `python3 -m pytest tests/test_project_docs.py::test_sprint_two_hundred_ninety_seven_documents_admin_api_token_load_guard -q` - 1 passed.
- `python3 -m ruff check src/jedi_devproject/runtime_config.py tests/test_runtime.py tests/test_project_docs.py` - all checks passed.
- `python3 -m mypy src/jedi_devproject/runtime_config.py tests/test_runtime.py tests/test_project_docs.py` - no issues found in 3 source files.
- `python3 -m ruff check src tests` - all checks passed.
- `python3 -m mypy src tests` - no issues found in 179 source files.
- `python3 -m pytest tests/test_project_docs.py -q` - 371 passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 1793 passed, total coverage 93.90%.
