# Sprint 459 Change Log

## Model provider response non-finite JSON rejection

Hardened OpenAI and Anthropic successful model-output parsing so provider responses cannot be
accepted when the model emits Python/JavaScript-style non-finite numeric constants: `NaN`,
`Infinity`, or `-Infinity`. Python `json.loads()` accepts those constants by default, which allowed
non-strict JSON model output to reach candidate normalization as ordinary floats.

Both adapters now use a shared strict JSON object loader from the provider contract. Non-finite
constants fail as the same fixed invalid-JSON provider diagnostic used for malformed JSON text, and
the diagnostic does not echo model-provided field names or values.

## Verification

- Added 2 failing-first provider response tests covering OpenAI `NaN` and Anthropic `Infinity`
  output rejection.
- `python3 -m pytest tests/test_openai_provider.py::test_openai_responses_provider_rejects_non_finite_response_json tests/test_anthropic_provider.py::test_anthropic_provider_rejects_non_finite_response_json -q`:
  failed before implementation because both providers accepted non-finite model output.
- `python3 -m pytest tests/test_openai_provider.py::test_openai_responses_provider_rejects_non_finite_response_json tests/test_openai_provider.py::test_openai_responses_provider_fails_closed_for_invalid_json tests/test_anthropic_provider.py::test_anthropic_provider_rejects_non_finite_response_json tests/test_anthropic_provider.py::test_anthropic_provider_fails_closed_for_invalid_json tests/test_anthropic_provider.py::test_anthropic_provider_fails_closed_for_non_object_json -q`:
  5 tests passed.
- `python3 -m ruff check src tests`: passed.
- `python3 -m mypy src tests`: passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 533 documentation tests passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`:
  2358 total tests passed at 93.82% coverage.
