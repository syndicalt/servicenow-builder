# Sprint 681 Change Log - Provider error envelope exact-dict boundary

## Scope

Hardened model provider API error diagnostics so OpenAI and Anthropic adapters only inspect exact JSON
dictionaries for upstream error envelopes. Dictionary subclasses are treated as absent structured error
details and fall back to status-only diagnostics.

## Tests First

- Added 2 failing-first provider error-envelope assertions:
  - `tests/test_openai_provider.py::test_openai_responses_provider_rejects_error_dict_subclass_without_leak`
  - `tests/test_anthropic_provider.py::test_anthropic_provider_rejects_error_dict_subclass_without_leak`
- Initial failures proved hostile upstream error dictionary subclasses could execute lookup hooks
  raising `client_secret=error-envelope-secret` before provider errors were raised.
- Added 1 failing-first documentation assertion:
  `tests/test_project_docs.py::test_sprint_681_documents_provider_error_envelope_exact_dict_boundary`
- Initial documentation failure proved this sprint log did not exist yet.

## Changes

- OpenAI API error diagnostics now require exact `dict` error envelopes before reading `message`,
  `type`, or `code`.
- Anthropic API error diagnostics now require exact `dict` error envelopes before reading `message`
  or `type`.
- Documented that malformed provider error envelope subclasses fall back to status-only diagnostics.

## Verification

- `python3 -m pytest tests/test_openai_provider.py::test_openai_responses_provider_rejects_error_dict_subclass_without_leak tests/test_anthropic_provider.py::test_anthropic_provider_rejects_error_dict_subclass_without_leak -q`
  failed first because provider API error diagnostics executed hostile dictionary-subclass lookup
  hooks and surfaced `client_secret=error-envelope-secret`.
- `python3 -m pytest tests/test_openai_provider.py::test_openai_responses_provider_rejects_error_dict_subclass_without_leak tests/test_openai_provider.py::test_openai_responses_provider_fails_closed_for_api_error tests/test_openai_provider.py::test_openai_responses_provider_reports_rate_limit_error_details tests/test_anthropic_provider.py::test_anthropic_provider_rejects_error_dict_subclass_without_leak tests/test_anthropic_provider.py::test_anthropic_provider_reports_error_type_without_message tests/test_anthropic_provider.py::test_anthropic_provider_redacts_and_bounds_error_details -q`
  passed, 6 tests.
- `python3 -m pytest tests/test_project_docs.py::test_sprint_681_documents_provider_error_envelope_exact_dict_boundary -q`
  failed first while this changelog was missing.
- `python3 -m pytest tests/test_openai_provider.py::test_openai_responses_provider_rejects_error_dict_subclass_without_leak tests/test_anthropic_provider.py::test_anthropic_provider_rejects_error_dict_subclass_without_leak tests/test_project_docs.py::test_sprint_681_documents_provider_error_envelope_exact_dict_boundary -q`
  passed, 3 tests.
- `ruff check src/jedi_devproject/openai_provider.py src/jedi_devproject/anthropic_provider.py tests/test_openai_provider.py tests/test_anthropic_provider.py tests/test_project_docs.py`
  passed.
- `mypy src/jedi_devproject/openai_provider.py src/jedi_devproject/anthropic_provider.py tests/test_openai_provider.py tests/test_anthropic_provider.py`
  passed across 4 source files.
- `python3 -m pytest tests/test_openai_provider.py tests/test_anthropic_provider.py -q` passed, 129 tests.
- `python3 -m pytest tests/test_project_docs.py -q` passed, 755 tests.
- `ruff check src tests` passed.
- `mypy src tests` passed across 197 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` passed,
  2903 tests with 93.11% total coverage.
