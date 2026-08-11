# Sprint 682 Change Log - Provider top-level response body exact-dict boundary

## Scope

Hardened model provider response handling so OpenAI and Anthropic adapters require exact JSON
dictionaries at the top-level `json_body` boundary before successful-output parsing or API error
diagnostic lookup. Dictionary subclasses are treated as malformed provider bodies instead of being
queried.

## Tests First

- Added 4 failing-first provider top-level body assertions:
  - `tests/test_openai_provider.py::test_openai_responses_provider_rejects_response_body_dict_subclass_without_leak`
  - `tests/test_openai_provider.py::test_openai_responses_provider_rejects_error_response_body_dict_subclass_without_leak`
  - `tests/test_anthropic_provider.py::test_anthropic_provider_rejects_response_body_dict_subclass_without_leak`
  - `tests/test_anthropic_provider.py::test_anthropic_provider_rejects_error_response_body_dict_subclass_without_leak`
- Initial failures proved hostile top-level response dictionary subclasses could execute lookup hooks
  raising `client_secret=response-body-secret` and `client_secret=error-body-secret` before provider
  errors were raised.
- Added 1 failing-first documentation assertion:
  `tests/test_project_docs.py::test_sprint_682_documents_provider_top_level_response_body_exact_dict_boundary`
- Initial documentation failure proved this sprint log did not exist yet.

## Changes

- OpenAI successful-response parsing now requires an exact `dict` body before reading output fields.
- OpenAI API error diagnostics now require an exact `dict` body before reading structured error details.
- Anthropic successful-response parsing now requires an exact `dict` body before reading stop reason
  or content fields.
- Anthropic API error diagnostics now require an exact `dict` body before reading structured error
  details.
- Documented exact top-level provider response body handling for both provider adapters.

## Verification

- `python3 -m pytest tests/test_openai_provider.py::test_openai_responses_provider_rejects_response_body_dict_subclass_without_leak tests/test_openai_provider.py::test_openai_responses_provider_rejects_error_response_body_dict_subclass_without_leak tests/test_anthropic_provider.py::test_anthropic_provider_rejects_response_body_dict_subclass_without_leak tests/test_anthropic_provider.py::test_anthropic_provider_rejects_error_response_body_dict_subclass_without_leak -q`
  failed first because provider parsing and API error diagnostics executed hostile top-level response
  body lookup hooks and surfaced `client_secret=response-body-secret` and
  `client_secret=error-body-secret`.
- `python3 -m pytest tests/test_openai_provider.py::test_openai_responses_provider_rejects_response_body_dict_subclass_without_leak tests/test_openai_provider.py::test_openai_responses_provider_rejects_error_response_body_dict_subclass_without_leak tests/test_openai_provider.py::test_openai_responses_provider_posts_structured_output_request tests/test_openai_provider.py::test_openai_responses_provider_fails_closed_for_api_error tests/test_anthropic_provider.py::test_anthropic_provider_rejects_response_body_dict_subclass_without_leak tests/test_anthropic_provider.py::test_anthropic_provider_rejects_error_response_body_dict_subclass_without_leak tests/test_anthropic_provider.py::test_anthropic_provider_posts_structured_output_request tests/test_anthropic_provider.py::test_anthropic_provider_reports_error_type_without_message -q`
  passed, 8 tests.
- `python3 -m pytest tests/test_project_docs.py::test_sprint_682_documents_provider_top_level_response_body_exact_dict_boundary -q`
  failed first while this changelog was missing.
- `python3 -m pytest tests/test_openai_provider.py::test_openai_responses_provider_rejects_response_body_dict_subclass_without_leak tests/test_openai_provider.py::test_openai_responses_provider_rejects_error_response_body_dict_subclass_without_leak tests/test_anthropic_provider.py::test_anthropic_provider_rejects_response_body_dict_subclass_without_leak tests/test_anthropic_provider.py::test_anthropic_provider_rejects_error_response_body_dict_subclass_without_leak tests/test_project_docs.py::test_sprint_682_documents_provider_top_level_response_body_exact_dict_boundary -q`
  passed, 5 tests.
- `ruff check src/jedi_devproject/openai_provider.py src/jedi_devproject/anthropic_provider.py tests/test_openai_provider.py tests/test_anthropic_provider.py tests/test_project_docs.py`
  passed.
- `mypy src/jedi_devproject/openai_provider.py src/jedi_devproject/anthropic_provider.py tests/test_openai_provider.py tests/test_anthropic_provider.py`
  passed across 4 source files.
- `python3 -m pytest tests/test_openai_provider.py tests/test_anthropic_provider.py -q` passed, 133 tests.
- `python3 -m pytest tests/test_project_docs.py -q` passed, 756 tests.
- `ruff check src tests` passed.
- `mypy src tests` passed across 197 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` passed,
  2908 tests with 93.12% total coverage.
