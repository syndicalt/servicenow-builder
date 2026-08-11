# Sprint 289 Change Log - Direct Model Provider Selector Diagnostics

## Summary

- Production validation now rejects direct `RuntimeSettings.model_provider` values containing whitespace or control characters before checking supported providers.
- Worker handler setup now rejects malformed direct provider selectors before unsupported-provider handling.
- Both paths return a fixed `JEDI_MODEL_PROVIDER` diagnostic and do not echo untrusted provider selector text.
- Existing env parsing, blank-provider no-model default, unsupported-provider rejection, and OpenAI credential/model guards remain intact.
- Added failing regressions proving malformed direct provider selectors previously surfaced raw selector text in runtime errors.
- Documented the direct provider-selector diagnostic boundary in the operator guide.

## Verification

- `python3 -m pytest tests/test_runtime.py -q -k "malformed_model_provider_without_echoing_value or malformed_provider_without_echoing_value"` - 2 tests failed before implementation because malformed direct provider selectors were echoed in runtime errors.
- `python3 -m pytest tests/test_runtime.py -q -k "malformed_model_provider_without_echoing_value or malformed_provider_without_echoing_value"` - 2 passed.
- `python3 -m pytest tests/test_runtime.py -q -k "malformed_model_provider_without_echoing_value or malformed_provider_without_echoing_value" && python3 -m pytest tests/test_project_docs.py::test_sprint_two_hundred_eighty_nine_documents_direct_model_provider_diagnostics -q` - 2 passed, then 1 passed.
- `python3 -m ruff check src/jedi_devproject/runtime_config.py src/jedi_devproject/runtime_fulfillment.py tests/test_runtime.py tests/test_project_docs.py` - all checks passed.
- `python3 -m mypy src/jedi_devproject/runtime_config.py src/jedi_devproject/runtime_fulfillment.py tests/test_runtime.py tests/test_project_docs.py` - success: no issues found in 4 source files.
- `python3 -m ruff check src tests` - all checks passed.
- `python3 -m mypy src tests` - success: no issues found in 179 source files.
- `python3 -m pytest tests/test_project_docs.py -q` - 363 passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 1757 passed; total coverage 93.89%.
