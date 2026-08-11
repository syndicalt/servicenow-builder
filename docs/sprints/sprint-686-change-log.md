# Sprint 686 Change Log - Anthropic error scalar exact-string boundary

## Scope

Hardened Anthropic API error diagnostics so structured error scalar fields are included only when
they are exact strings. The response body, nested error envelope, and response headers already had
exact-boundary protections; this sprint closes the remaining API error scalar boundary for
`message` and `type`.

## Tests First

- Added 2 failing-first Anthropic error-scalar assertions:
  - `tests/test_anthropic_provider.py::test_anthropic_provider_rejects_error_message_subclass_diagnostic`
  - `tests/test_anthropic_provider.py::test_anthropic_provider_rejects_error_type_subclass_diagnostic`
- Initial failures proved Anthropic diagnostics still accepted string subclasses, including
  `client_secret=message-secret`, and surfaced subclass-backed `type` metadata.
- Added 1 failing-first documentation assertion:
  `tests/test_project_docs.py::test_sprint_686_documents_anthropic_error_scalar_exact_string_boundary`
- Initial documentation failure proved this sprint log did not exist yet.

## Changes

- Anthropic API error `message` and `type` fields now require `type(value) is str` before redaction
  or metadata normalization.
- Ordinary exact-string Anthropic error diagnostics remain visible for operator triage.
- Non-exact diagnostic scalars are skipped rather than stringified, normalized, or surfaced.
- Documented the Anthropic error scalar boundary in the operator guide.

## Verification

- `python3 -m pytest tests/test_anthropic_provider.py -q -k "error_message_subclass or error_type_subclass"`
  failed first because string subclasses were included in diagnostics.
- `python3 -m pytest tests/test_anthropic_provider.py -q -k "reports_error_type_without_message or redacts_api_key_from_error_paths or redacts_and_bounds_error_details or sanitizes_structured_error_type_diagnostic or error_message_subclass or error_type_subclass"`
  passed, 6 tests.
- `python3 -m pytest tests/test_project_docs.py -q -k sprint_686`
  failed first while this changelog was missing.
- `python3 -m pytest tests/test_project_docs.py -q -k "sprint_685 or sprint_686"` passed, 2 tests.
- `python3 -m pytest tests/test_anthropic_provider.py tests/test_openai_provider.py -q` passed,
  141 tests.
- `ruff check src tests` passed.
- `mypy src tests` passed across 197 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` passed,
  2924 tests with 93.14% total coverage.
