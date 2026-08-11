# Sprint 689 Change Log - Provider response status-code HTTP-range boundary

## Scope

Hardened provider response classification so exact integer status codes must also be valid HTTP
status values. Sprint 688 ensured `status_code` cannot be a custom object; this sprint prevents
out-of-range exact integers from being classified as successful responses or upstream provider
failures.

## Tests First

- Added 4 failing-first provider status-code range assertions:
  - `tests/test_openai_provider.py::test_openai_responses_provider_rejects_status_code_outside_http_range[99]`
  - `tests/test_openai_provider.py::test_openai_responses_provider_rejects_status_code_outside_http_range[600]`
  - `tests/test_anthropic_provider.py::test_anthropic_provider_rejects_status_code_outside_http_range[99]`
  - `tests/test_anthropic_provider.py::test_anthropic_provider_rejects_status_code_outside_http_range[600]`
- Initial failures proved `99` could be treated as a successful OpenAI response and `600` could be
  surfaced as an upstream OpenAI failure instead of being rejected as malformed transport state.
- Added 1 failing-first documentation assertion:
  `tests/test_project_docs.py::test_sprint_689_documents_provider_status_code_http_range_boundary`
- Initial documentation failure proved this sprint log did not exist yet.

## Changes

- OpenAI response status validation now rejects exact integers below 100 or above 599 with a fixed
  provider diagnostic.
- Anthropic response status validation now rejects exact integers below 100 or above 599 before retry
  classification or success/error branching.
- Existing exact-integer status-code protections remain in place.
- Documented the provider HTTP status-code range boundary in the operator guide.

## Verification

- `python3 -m pytest tests/test_openai_provider.py -q -k "outside_http_range"` failed first because
  out-of-range status integers were classified instead of rejected.
- `python3 -m pytest tests/test_openai_provider.py -q -k "outside_http_range or status_code_object or posts_structured_output_request or fails_closed_for_api_error" && python3 -m pytest tests/test_anthropic_provider.py -q -k "outside_http_range or status_code_object or posts_structured_output_request or reports_error_type_without_message"`
  passed, 10 tests.
- `python3 -m pytest tests/test_project_docs.py -q -k sprint_689`
  failed first while this changelog was missing.
- `python3 -m pytest tests/test_project_docs.py -q -k sprint_689` passed, 1 test.
- `python3 -m pytest tests/test_openai_provider.py tests/test_anthropic_provider.py -q` passed,
  149 tests.
- `ruff check src tests` passed.
- `mypy src tests` passed across 197 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` passed,
  2935 tests with 93.15% total coverage.
