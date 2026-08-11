# Sprint 290 Change Log - Model Provider Selector Bounds

## Summary

- Added a shared `MAX_MODEL_PROVIDER_CHARS` bound of 256 characters for `JEDI_MODEL_PROVIDER`.
- Env parsing, production validation, and worker handler setup now reject oversized provider selectors before unsupported-provider handling.
- Unsupported provider selectors now return a fixed `Unsupported JEDI_MODEL_PROVIDER` diagnostic instead of echoing arbitrary selector text.
- Existing blank-provider no-model default, whitespace/control-character rejection, OpenAI provider activation, and OpenAI credential/model guards remain intact.
- Added failing regressions proving oversized and unsupported provider selectors were previously reflected in runtime diagnostics.
- Documented the provider selector length and unsupported-diagnostic boundary in the operator guide.

## Verification

- `python3 -m pytest tests/test_runtime.py -q -k "oversized_model_provider_without_echoing_value or unsupported_model_provider_without_echoing_value or unsupported_provider_without_echoing_value"` - 3 tests failed before implementation because oversized and unsupported provider selectors were reflected in runtime diagnostics.
- `python3 -m pytest tests/test_runtime.py -q -k "oversized_model_provider_without_echoing_value or unsupported_model_provider_without_echoing_value or unsupported_provider_without_echoing_value"` - 3 passed.
- `python3 -m pytest tests/test_runtime.py -q -k "model_provider_env_value or oversized_model_provider_without_echoing_value or unsupported_model_provider_without_echoing_value or unsupported_provider_without_echoing_value"` - 4 passed.
- `python3 -m pytest tests/test_runtime.py -q -k "model_provider_env_value or oversized_model_provider_without_echoing_value or unsupported_model_provider_without_echoing_value or unsupported_provider_without_echoing_value" && python3 -m pytest tests/test_project_docs.py::test_sprint_two_hundred_ninety_documents_model_provider_selector_bounds -q` - 4 passed, then 1 passed.
- `python3 -m ruff check src/jedi_devproject/runtime_config.py src/jedi_devproject/runtime_fulfillment.py tests/test_runtime.py tests/test_project_docs.py` - all checks passed.
- `python3 -m mypy src/jedi_devproject/runtime_config.py src/jedi_devproject/runtime_fulfillment.py tests/test_runtime.py tests/test_project_docs.py` - success: no issues found in 4 source files.
- `python3 -m ruff check src tests` - all checks passed.
- `python3 -m mypy src tests` - success: no issues found in 179 source files.
- `python3 -m pytest tests/test_project_docs.py -q` - 364 passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 1762 passed; total coverage 93.91%.
