# Sprint 685 Change Log - OpenAI error scalar exact-string boundary

## Scope

Hardened OpenAI API error diagnostics so structured error scalar fields are included only when they
are exact strings. The error response body and nested error envelope were already exact dictionaries;
this sprint closes the remaining scalar boundary for `message`, `type`, and `code`.

## Tests First

- Added 3 failing-first OpenAI error-scalar assertions:
  - `tests/test_openai_provider.py::test_openai_responses_provider_rejects_error_message_subclass_diagnostic`
  - `tests/test_openai_provider.py::test_openai_responses_provider_rejects_error_type_subclass_diagnostic`
  - `tests/test_openai_provider.py::test_openai_responses_provider_rejects_error_code_subclass_diagnostic`
- Initial failures proved OpenAI diagnostics still accepted string subclasses, including
  `client_secret=message-secret`, and surfaced subclass-backed `type` and `code` metadata.
- Added 1 failing-first documentation assertion:
  `tests/test_project_docs.py::test_sprint_685_documents_openai_error_scalar_exact_string_boundary`
- Initial documentation failure proved this sprint log did not exist yet.

## Changes

- OpenAI API error `message`, `type`, and `code` fields now require `type(value) is str` before
  redaction or metadata normalization.
- Ordinary exact-string OpenAI error diagnostics remain visible for operator triage.
- Non-exact diagnostic scalars are skipped rather than stringified, normalized, or surfaced.
- Documented the OpenAI error scalar boundary in the operator guide.

## Verification

- `python3 -m pytest tests/test_openai_provider.py -q -k "error_message_subclass or error_type_subclass or error_code_subclass"`
  failed first because string subclasses were included in diagnostics.
- `python3 -m pytest tests/test_openai_provider.py -q -k "fails_closed_for_api_error or reports_rate_limit_error_details or redacts_and_bounds_error_details or redacts_structured_error_metadata or error_message_subclass or error_type_subclass or error_code_subclass"`
  passed, 7 tests.
- `python3 -m pytest tests/test_project_docs.py -q -k sprint_685`
  failed first while this changelog was missing.
- `python3 -m pytest tests/test_project_docs.py -q -k sprint_685` passed, 1 test.
- `python3 -m pytest tests/test_openai_provider.py -q` passed, 47 tests.
- `ruff check src tests` passed.
- `mypy src tests` passed across 197 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` passed,
  2921 tests with 93.14% total coverage.
