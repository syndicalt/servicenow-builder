# Sprint 287 Change Log - OpenAI Runtime Provider Config Errors

## Summary

- Worker-side OpenAI provider construction now wraps direct `OpenAIProviderSettings` validation failures as `RuntimeConfigError`.
- Runtime errors name the malformed setting (`OPENAI_API_KEY`, `OPENAI_MODEL`, or future OpenAI provider fields) without including provider values or Pydantic input diagnostics.
- Malformed direct `RuntimeSettings` wiring now fails before job claim, ServiceNow calls, or model transport calls.
- Existing `.env` parsing, production startup validation, and direct provider settings guards remain intact.
- Added failing regressions proving malformed direct OpenAI runtime settings previously surfaced raw provider validation errors.
- Documented the runtime provider config error boundary in the operator guide.

## Verification

- `python3 -m pytest tests/test_runtime.py -q -k wraps_invalid_openai_provider_settings` - 2 tests failed before implementation because malformed direct OpenAI runtime settings surfaced raw provider validation errors.
- `python3 -m pytest tests/test_runtime.py -q -k wraps_invalid_openai_provider_settings` - 2 passed.
- `python3 -m pytest tests/test_runtime.py -q -k wraps_invalid_openai_provider_settings && python3 -m pytest tests/test_project_docs.py::test_sprint_two_hundred_eighty_seven_documents_openai_runtime_config_errors -q` - 2 passed, then 1 passed.
- `python3 -m ruff check src/jedi_devproject/runtime_fulfillment.py tests/test_runtime.py tests/test_project_docs.py` - all checks passed.
- `python3 -m mypy src/jedi_devproject/runtime_fulfillment.py tests/test_runtime.py tests/test_project_docs.py` - success: no issues found in 3 source files.
- `python3 -m ruff check src tests` - all checks passed.
- `python3 -m mypy src tests` - success: no issues found in 179 source files.
- `python3 -m pytest tests/test_project_docs.py -q` - 361 passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 1750 passed; total coverage 93.88%.
