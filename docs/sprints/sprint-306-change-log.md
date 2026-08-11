# Sprint 306 Change Log - Update Set Username Settings Load Guard

## Summary

- Runtime settings loading now rejects malformed `JEDI_UPDATE_SET_USER_NAME` values before settings are returned.
- `JEDI_UPDATE_SET_USER_NAME` must be non-empty, unpadded, and free of control characters when configured.
- Empty or absent values still behave as unconfigured, preserving the existing production requirement that the legacy `JEDI_UPDATE_SET_APPLY=true` path must provide an operator identity.
- Malformed update-set username diagnostics name only the setting and do not echo padded or control-character fragments.
- Existing direct `RuntimeSettings` production validation remains intact for non-env wiring.
- Added failing regressions proving padded and control-character `JEDI_UPDATE_SET_USER_NAME` env values were previously normalized during settings loading.
- Documented the update-set username settings-load boundary in the operator guide.

## Verification

- `python3 -m pytest tests/test_runtime.py -q -k "update_set_user_name or update_set_apply_controls or update_set_apply_operator"` - 3 tests failed before implementation because malformed update-set usernames were normalized during settings loading.
- `python3 -m pytest tests/test_runtime.py -q -k "update_set_user_name or update_set_apply_controls or update_set_apply_operator"` - 5 passed after implementation.
- `python3 -m pytest tests/test_runtime.py -q` - 243 passed.
- `python3 -m pytest tests/test_project_docs.py::test_sprint_three_hundred_six_documents_update_set_username_load_guard -q` - 1 passed.
- `python3 -m ruff check src/jedi_devproject/runtime_config.py tests/test_runtime.py tests/test_project_docs.py` - all checks passed.
- `python3 -m mypy src/jedi_devproject/runtime_config.py tests/test_runtime.py tests/test_project_docs.py` - no issues found in 3 source files.
- `python3 -m ruff check src tests` - all checks passed.
- `python3 -m mypy src tests` - no issues found in 179 source files.
- `python3 -m pytest tests/test_project_docs.py -q` - 380 passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 1829 passed, total coverage 93.91%.
