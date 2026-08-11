# Sprint 286 Change Log - OpenAI Env Whitespace Fail-Closed

## Summary

- OpenAI runtime env parsing now rejects non-empty values with leading or trailing whitespace instead of silently trimming them.
- `OPENAI_API_KEY` and `OPENAI_MODEL` use the same fail-closed whitespace boundary when `load_runtime_settings()` reads the runtime environment.
- Blank `OPENAI_API_KEY` and `OPENAI_MODEL` values still behave as absent so existing missing-secret validation remains authoritative when `JEDI_MODEL_PROVIDER=openai`.
- OpenAI env-derived values now reuse the same provider setting guards as direct `OpenAIProviderSettings` construction: empty, oversized, whitespace, and control-character validation.
- Added failing regressions proving malformed OpenAI env values were previously accepted after normalization.
- Documented the OpenAI env whitespace boundary in the operator guide.

## Verification

- `python3 -m pytest tests/test_runtime.py -q -k openai_env_values_with_boundary_whitespace` - 4 tests failed before implementation because malformed OpenAI env values were accepted after normalization.
- `python3 -m pytest tests/test_runtime.py -q -k openai_env_values_with_boundary_whitespace` - 4 passed.
- `python3 -m pytest tests/test_runtime.py -q -k openai_env_values_with_boundary_whitespace && python3 -m pytest tests/test_project_docs.py::test_sprint_two_hundred_eighty_six_documents_openai_env_whitespace -q` - 4 passed, then 1 passed.
- `python3 -m ruff check src/jedi_devproject/runtime_config.py tests/test_runtime.py tests/test_project_docs.py` - all checks passed.
- `python3 -m mypy src/jedi_devproject/runtime_config.py tests/test_runtime.py tests/test_project_docs.py` - success: no issues found in 3 source files.
- `python3 -m ruff check src tests` - all checks passed.
- `python3 -m mypy src tests` - success: no issues found in 179 source files.
- `python3 -m pytest tests/test_project_docs.py -q` - 360 passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 1747 passed; total coverage 93.93%.
