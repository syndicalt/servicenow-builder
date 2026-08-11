# Sprint 296 Change Log - Admin Console Credential Settings Load Guard

## Summary

- Runtime settings loading now rejects malformed development Basic-auth admin console credentials.
- `JEDI_ADMIN_CONSOLE_USERNAME` and `JEDI_ADMIN_CONSOLE_PASSWORD` must be unpadded and free of control characters before runtime settings are returned.
- Blank or absent admin console credential values still behave as unconfigured, preserving the fail-closed admin console path.
- Malformed admin console credential diagnostics name only the setting and do not echo credential fragments.
- Existing production validation still rejects `JEDI_ADMIN_AUTH_MODE=dev_basic`.
- Added failing regressions proving padded and control-character admin console credential env values were previously accepted during settings loading.
- Documented the admin console credential settings-load boundary in the operator guide.

## Verification

- `python3 -m pytest tests/test_runtime.py -q -k "admin_console_credentials and load_runtime_settings"` - 3 tests failed before implementation because malformed admin console credentials were accepted during settings loading.
- `python3 -m pytest tests/test_runtime.py -q -k "admin_console_credentials and load_runtime_settings"` - 4 passed after implementation.
- `python3 -m pytest tests/test_runtime.py -q -k "admin_console or admin_auth"` - 34 passed.
- `python3 -m pytest tests/test_project_docs.py::test_sprint_two_hundred_ninety_six_documents_admin_console_credential_load_guard -q` - 1 passed.
- `python3 -m ruff check src/jedi_devproject/runtime_config.py tests/test_runtime.py tests/test_project_docs.py` - all checks passed.
- `python3 -m mypy src/jedi_devproject/runtime_config.py tests/test_runtime.py tests/test_project_docs.py` - no issues found in 3 source files.
- `python3 -m ruff check src tests` - all checks passed.
- `python3 -m mypy src tests` - no issues found in 179 source files.
- `python3 -m pytest tests/test_project_docs.py -q` - 370 passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 1789 passed, total coverage 93.90%.
