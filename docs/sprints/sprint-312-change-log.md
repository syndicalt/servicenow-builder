# Sprint 312 Change Log - Project Config Value Hygiene

## Summary

- Project TOML loading now validates required values before returning `AppConfig`.
- `servicenow_instance_url` must be an HTTPS ServiceNow URL without credentials, fragments, raw whitespace/control characters, or encoded whitespace/control characters.
- `artifact_dir` and `target_boundary` must be unpadded and free of control characters.
- Internal spaces remain allowed for `target_boundary`, preserving values such as `FedRAMP Moderate`.
- Malformed project config diagnostics name only the setting and do not echo URL credentials or configured value fragments.
- Existing required-setting validation and the 1 MiB bounded TOML read remain intact.
- Added failing regressions proving malformed ServiceNow URLs, padded artifact paths, and padded/control-character target boundaries were previously accepted during project config loading.
- Documented the project config value hygiene boundary in the operator guide.

## Verification

- `python3 -m pytest tests/test_config.py -q` - 8 tests failed before implementation because malformed required project config values were accepted.
- `python3 -m pytest tests/test_config.py -q` - 11 passed after implementation.
- `python3 -m ruff check src/jedi_devproject/config.py tests/test_config.py` - all checks passed.
- `python3 -m mypy src/jedi_devproject/config.py tests/test_config.py` - no issues found in 2 source files.
- `python3 -m pytest tests/test_project_docs.py::test_sprint_three_hundred_twelve_documents_project_config_value_hygiene -q` - 1 passed.
- `python3 -m ruff check src/jedi_devproject/config.py tests/test_config.py tests/test_project_docs.py` - all checks passed.
- `python3 -m mypy src/jedi_devproject/config.py tests/test_config.py tests/test_project_docs.py` - no issues found in 3 source files.
- `python3 -m ruff check src tests` - all checks passed.
- `python3 -m mypy src tests` - no issues found in 179 source files.
- `python3 -m pytest tests/test_project_docs.py -q` - 386 passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 1866 passed, total coverage 93.91%.
