# Sprint 751 Change Log - Runtime OpenAI provider setting cause boundary

## Scope

Hardened runtime OpenAI provider setting validation so `OPENAI_API_KEY` and `OPENAI_MODEL` parser failures cannot stringify hostile provider validation exceptions or retain them as public `RuntimeConfigError` causes.

## Tests First

- Added 2 failing-first runtime OpenAI provider setting cause assertions:
  - `tests/test_runtime.py::test_runtime_config_openai_api_key_wraps_unstringifiable_provider_errors`
  - `tests/test_runtime.py::test_runtime_config_openai_model_wraps_unstringifiable_provider_errors`
- Initial failures proved `_optional_openai_provider_value()` interpolated the original provider validation error, allowing secondary `ValueError` failures containing `openai-client-secret-value`.
- Added 1 failing-first documentation assertion:
  `tests/test_project_docs.py::test_sprint_751_documents_runtime_openai_provider_setting_cause_boundary`
- Initial documentation failure proved this sprint log did not exist yet.

## Changes

- Wrapped OpenAI provider setting validation errors with `exception_diagnostic_message()`.
- Suppressed original provider validation causes when raising `RuntimeConfigError`.
- Preserved setting-specific diagnostics for `OPENAI_API_KEY` and `OPENAI_MODEL`.
- Documented the runtime OpenAI provider setting cause boundary in the operator guide.

## Verification

- `python3 -m pytest tests/test_runtime.py -q -k "runtime_config_openai_api_key_wraps_unstringifiable_provider_errors or runtime_config_openai_model_wraps_unstringifiable_provider_errors"` failed first, then passed.
- `python3 -m pytest tests/test_project_docs.py -q -k sprint_751` failed first, then passed.
- `ruff check src tests` passed.
- `mypy src tests` passed.
- `python3 -m pytest tests/test_runtime.py -q -k "runtime_config or openai_provider_setting"` passed: 6 passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` passed: 3084 passed, 93.35% coverage.
