# Sprint 678 Change Log - Provider response text exact-string boundary

## Scope

Hardened model provider response text parsing so OpenAI and Anthropic adapters only parse exact JSON
strings returned by trusted JSON decoding, not string subclasses that can execute custom hooks during
length checks, string conversion, or JSON parsing setup.

## Tests First

- Added 3 failing-first provider response-text assertions:
  - `tests/test_openai_provider.py::test_openai_responses_provider_rejects_string_subclass_output_text_without_leak`
  - `tests/test_openai_provider.py::test_openai_responses_provider_rejects_string_subclass_nested_text_without_leak`
  - `tests/test_anthropic_provider.py::test_anthropic_provider_rejects_string_subclass_text_block_without_leak`
- Initial failures proved hostile output text could execute hooks raising
  `client_secret=output-text-secret`, `client_secret=nested-output-secret`, and
  `client_secret=text-block-secret` before provider errors were raised.
- Added 1 failing-first documentation assertion:
  `tests/test_project_docs.py::test_sprint_678_documents_provider_response_text_exact_string_boundary`
- Initial documentation failure proved this sprint log did not exist yet.

## Changes

- OpenAI direct `output_text` parsing now requires `type(output_text) is str`.
- OpenAI nested `output[].content[].text` parsing now requires exact `str` and passes it through
  without `str()` conversion.
- Anthropic text content block parsing now requires exact `str` and passes it through without
  `str()` conversion.
- Documented exact-string model response text parsing for both provider adapters.

## Verification

- `python3 -m pytest tests/test_openai_provider.py::test_openai_responses_provider_rejects_string_subclass_output_text_without_leak tests/test_openai_provider.py::test_openai_responses_provider_rejects_string_subclass_nested_text_without_leak tests/test_anthropic_provider.py::test_anthropic_provider_rejects_string_subclass_text_block_without_leak -q`
  failed first because provider parsing executed hostile string subclass hooks and surfaced
  `client_secret=output-text-secret`, `client_secret=nested-output-secret`, and
  `client_secret=text-block-secret`.
- `python3 -m pytest tests/test_openai_provider.py::test_openai_responses_provider_rejects_string_subclass_output_text_without_leak tests/test_openai_provider.py::test_openai_responses_provider_rejects_string_subclass_nested_text_without_leak tests/test_openai_provider.py::test_openai_responses_provider_posts_structured_output_request tests/test_anthropic_provider.py::test_anthropic_provider_rejects_string_subclass_text_block_without_leak -q`
  passed, 4 tests.
- `python3 -m pytest tests/test_openai_provider.py::test_openai_responses_provider_posts_structured_output_request tests/test_anthropic_provider.py::test_anthropic_provider_posts_structured_output_request -q`
  passed, 2 tests.
- `python3 -m pytest tests/test_project_docs.py::test_sprint_678_documents_provider_response_text_exact_string_boundary -q`
  failed first while this changelog was missing.
- `python3 -m pytest tests/test_openai_provider.py::test_openai_responses_provider_rejects_string_subclass_output_text_without_leak tests/test_openai_provider.py::test_openai_responses_provider_rejects_string_subclass_nested_text_without_leak tests/test_anthropic_provider.py::test_anthropic_provider_rejects_string_subclass_text_block_without_leak tests/test_project_docs.py::test_sprint_678_documents_provider_response_text_exact_string_boundary -q`
  passed, 4 tests.
- `ruff check src/jedi_devproject/openai_provider.py src/jedi_devproject/anthropic_provider.py tests/test_openai_provider.py tests/test_anthropic_provider.py tests/test_project_docs.py`
  passed.
- `mypy src/jedi_devproject/openai_provider.py src/jedi_devproject/anthropic_provider.py tests/test_openai_provider.py tests/test_anthropic_provider.py`
  passed across 4 source files.
- `python3 -m pytest tests/test_openai_provider.py tests/test_anthropic_provider.py -q` passed, 121 tests.
- `python3 -m pytest tests/test_project_docs.py -q` passed, 752 tests.
- `ruff check src tests` passed.
- `mypy src tests` passed across 197 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` passed,
  2892 tests with 93.05% total coverage.
