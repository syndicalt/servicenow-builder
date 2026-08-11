# Sprint 690 Change Log - Provider transport response object exact-type boundary

## Scope

Hardened provider transport ingress so OpenAI and Anthropic adapters validate the response object
type before reading `status_code`, headers, or JSON body fields. Sprint 688 and Sprint 689 hardened
the status value itself; this sprint closes the object boundary around alternate or corrupted
transport responses.

## Tests First

- Added 2 failing-first provider response-object assertions:
  - `tests/test_openai_provider.py::test_openai_responses_provider_rejects_response_object_without_leak`
  - `tests/test_anthropic_provider.py::test_anthropic_provider_rejects_response_object_without_leak`
- Initial failures proved arbitrary response objects could execute hostile `status_code` property
  hooks raising `client_secret=response-object-secret` before provider response classification failed
  closed.
- Added 1 failing-first documentation assertion:
  `tests/test_project_docs.py::test_sprint_690_documents_provider_response_object_exact_type_boundary`
- Initial documentation failure proved this sprint log did not exist yet.

## Changes

- OpenAI transport responses must be exact `HttpResponse` objects before status or body access.
- Anthropic transport responses must be exact `HttpResponse` or `AnthropicHttpResponse` objects
  before retry classification, status checks, header lookup, or body parsing.
- Arbitrary response objects fail with fixed provider diagnostics and are not stringified or
  reflected.
- Documented the provider transport response object boundary in the operator guide.

## Verification

- `python3 -m pytest tests/test_openai_provider.py::test_openai_responses_provider_rejects_response_object_without_leak tests/test_anthropic_provider.py::test_anthropic_provider_rejects_response_object_without_leak -q`
  failed first because hostile response attribute hooks executed.
- `python3 -m pytest tests/test_openai_provider.py -q -k "response_object_without_leak or status_code_object or outside_http_range or posts_structured_output_request or fails_closed_for_api_error" && python3 -m pytest tests/test_anthropic_provider.py -q -k "response_object_without_leak or status_code_object or outside_http_range or posts_structured_output_request or reports_error_type_without_message"`
  passed, 12 tests.
- `python3 -m pytest tests/test_project_docs.py -q -k sprint_690`
  failed first while this changelog was missing.
- `python3 -m pytest tests/test_project_docs.py -q -k sprint_690` passed, 1 test.
- `python3 -m pytest tests/test_openai_provider.py tests/test_anthropic_provider.py -q` passed,
  151 tests.
- `ruff check src tests` passed.
- `mypy src tests` passed across 197 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` passed,
  2938 tests with 93.15% total coverage.
