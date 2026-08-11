# Sprint 292 Change Log - Runtime Environment Switch Fail-Closed

## Summary

- `JEDI_ENVIRONMENT` env parsing now rejects non-empty values with leading, trailing, or internal whitespace/control characters instead of silently trimming them.
- Case-insensitive `development` and `production` values remain supported and are stored normalized to lowercase.
- Direct `RuntimeSettings.runtime_environment` wiring is now validated before `validate_runtime_settings()` decides whether production checks apply.
- Malformed direct runtime environment values now fail with fixed `JEDI_ENVIRONMENT` diagnostics instead of silently skipping production validation.
- Existing development default behavior, production posture checks, and malformed-name validation remain intact.
- Added failing regressions proving padded env values were previously normalized and malformed direct runtime environment values could bypass production validation.
- Documented the runtime environment switch boundary in the operator guide.

## Verification

- `python3 -m pytest tests/test_runtime.py -q -k "runtime_environment_whitespace or malformed_runtime_environment_without_skipping"` - 4 tests failed before implementation because padded env values were normalized and malformed direct runtime environment values skipped production validation.
- `python3 -m pytest tests/test_runtime.py -q -k "runtime_environment_whitespace or malformed_runtime_environment_without_skipping"` - 4 passed.
- `python3 -m pytest tests/test_runtime.py -q -k "runtime_environment_whitespace or malformed_runtime_environment_without_skipping" && python3 -m pytest tests/test_project_docs.py::test_sprint_two_hundred_ninety_two_documents_runtime_environment_switch -q` - 4 passed, then 1 passed.
- `python3 -m ruff check src/jedi_devproject/runtime_config.py tests/test_runtime.py tests/test_project_docs.py` - all checks passed.
- `python3 -m mypy src/jedi_devproject/runtime_config.py tests/test_runtime.py tests/test_project_docs.py` - success: no issues found in 3 source files.
- `python3 -m ruff check src tests` - all checks passed.
- `python3 -m mypy src tests` - success: no issues found in 179 source files.
- `python3 -m pytest tests/test_project_docs.py -q` - 366 passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 1773 passed; total coverage 93.91%.
