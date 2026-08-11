# Sprint 288 Change Log - Model Provider Selector Whitespace Fail-Closed

## Summary

- `JEDI_MODEL_PROVIDER` env parsing now rejects non-empty values with leading, trailing, or internal whitespace/control characters instead of silently trimming them.
- Blank `JEDI_MODEL_PROVIDER` values still behave as absent, preserving the default no-model-calls posture.
- Padded provider selectors can no longer accidentally activate `openai` after dotenv normalization.
- Existing OpenAI credential/model env guards and production startup provider validation remain intact.
- Added failing regressions proving malformed provider selector env values were previously accepted after normalization.
- Documented the provider selector whitespace boundary in the operator guide.

## Verification

- `python3 -m pytest tests/test_runtime.py -q -k model_provider_env_whitespace` - 3 tests failed before implementation because malformed provider selector env values were accepted after normalization.
- `python3 -m pytest tests/test_runtime.py -q -k model_provider_env_whitespace` - 3 passed.
- `python3 -m pytest tests/test_runtime.py -q -k model_provider_env_whitespace && python3 -m pytest tests/test_project_docs.py::test_sprint_two_hundred_eighty_eight_documents_model_provider_selector_whitespace -q` - 3 passed, then 1 passed.
- `python3 -m ruff check src/jedi_devproject/runtime_config.py tests/test_runtime.py tests/test_project_docs.py` - all checks passed.
- `python3 -m mypy src/jedi_devproject/runtime_config.py tests/test_runtime.py tests/test_project_docs.py` - success: no issues found in 3 source files.
- `python3 -m ruff check src tests` - all checks passed.
- `python3 -m mypy src tests` - success: no issues found in 179 source files.
- `python3 -m pytest tests/test_project_docs.py -q` - 362 passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 1754 passed; total coverage 93.89%.
