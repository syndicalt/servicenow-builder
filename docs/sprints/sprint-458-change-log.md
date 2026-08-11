# Sprint 458 Change Log

## Model provider prompt payload non-finite number rejection

Hardened the OpenAI and Anthropic implementation-candidate providers so prompt payloads cannot
serialize Python non-finite floats into model context as `NaN`, `Infinity`, or `-Infinity`.
Both adapters now use a shared strict implementation-payload serializer from the provider contract,
preserving the existing byte-identical prompt payload guarantee between providers.

Malformed payloads fail before transport send with the provider-native error type and a stable
diagnostic: `Model provider prompt payload contains non-finite numeric values`. The diagnostic does
not echo payload field names, values, or credential-like payload strings.

## Verification

- Added 2 failing-first provider prompt payload tests covering OpenAI and Anthropic non-finite
  prompt payload rejection before transport send.
- `python3 -m pytest tests/test_openai_provider.py::test_openai_responses_provider_rejects_non_finite_prompt_payload_before_transport tests/test_anthropic_provider.py::test_anthropic_provider_rejects_non_finite_prompt_payload_before_transport -q`:
  failed before implementation because OpenAI sent the malformed prompt and failed later on response
  parsing, while Anthropic sent the malformed prompt and completed.
- `python3 -m pytest tests/test_openai_provider.py::test_openai_responses_provider_rejects_non_finite_prompt_payload_before_transport tests/test_anthropic_provider.py::test_anthropic_provider_rejects_non_finite_prompt_payload_before_transport tests/test_anthropic_provider.py::test_anthropic_provider_sends_same_instructions_and_payload_as_openai -q`:
  3 tests passed.
- `python3 -m ruff check src tests`: passed.
- `python3 -m mypy src tests`: passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 532 documentation tests passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`:
  2355 total tests passed at 93.81% coverage.
