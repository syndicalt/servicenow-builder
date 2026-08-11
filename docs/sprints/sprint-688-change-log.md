# Sprint 688 Change Log - Provider response status-code exact-integer boundary

## Scope

Hardened provider response classification so OpenAI and Anthropic response status codes must be exact
integers before retry, success, or error branching. This closes the branch boundary around
`status_code >= 400` and Anthropic retryable-status checks.

## Tests First

- Added 2 failing-first provider status-code assertions:
  - `tests/test_openai_provider.py::test_openai_responses_provider_rejects_status_code_object_without_leak`
  - `tests/test_anthropic_provider.py::test_anthropic_provider_rejects_status_code_object_without_leak`
- Initial failures proved status-code objects could execute hostile comparison hooks raising
  `client_secret=status-code-secret` before provider response classification failed closed.
- Added 1 failing-first documentation assertion:
  `tests/test_project_docs.py::test_sprint_688_documents_provider_status_code_exact_integer_boundary`
- Initial documentation failure proved this sprint log did not exist yet.

## Changes

- OpenAI responses now validate `status_code` with an exact-integer check before success/error
  branching.
- Anthropic responses now validate `status_code` with an exact-integer check before retry
  classification and before success/error branching.
- Non-integer status values fail with provider-specific fixed diagnostics and are not compared,
  stringified, or surfaced.
- Documented the provider response status-code boundary in the operator guide.

## Verification

- `python3 -m pytest tests/test_openai_provider.py::test_openai_responses_provider_rejects_status_code_object_without_leak tests/test_anthropic_provider.py::test_anthropic_provider_rejects_status_code_object_without_leak -q`
  failed first because hostile status-code comparison hooks executed.
- `python3 -m pytest tests/test_openai_provider.py::test_openai_responses_provider_rejects_status_code_object_without_leak tests/test_anthropic_provider.py::test_anthropic_provider_rejects_status_code_object_without_leak tests/test_openai_provider.py::test_openai_responses_provider_posts_structured_output_request tests/test_openai_provider.py::test_openai_responses_provider_fails_closed_for_api_error tests/test_anthropic_provider.py::test_anthropic_provider_posts_structured_output_request tests/test_anthropic_provider.py::test_anthropic_provider_reports_error_type_without_message -q`
  passed, 6 tests.
- `python3 -m pytest tests/test_project_docs.py -q -k sprint_688`
  failed first while this changelog was missing.
- `python3 -m pytest tests/test_project_docs.py -q -k sprint_688` passed, 1 test.
- `python3 -m pytest tests/test_openai_provider.py tests/test_anthropic_provider.py -q` passed,
  145 tests.
- `ruff check src tests` passed.
- `mypy src tests` passed across 197 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` passed,
  2930 tests with 93.15% total coverage.
