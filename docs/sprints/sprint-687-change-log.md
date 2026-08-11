# Sprint 687 Change Log - Provider content type-marker exact-string boundary

## Scope

Hardened successful provider response text selection so OpenAI and Anthropic content `type` markers
must be exact strings before comparison. The response body, collection containers, content items, and
text values already had exact-boundary protections; this sprint closes the marker comparison gap.

## Tests First

- Added 2 failing-first provider content type-marker assertions:
  - `tests/test_openai_provider.py::test_openai_responses_provider_rejects_content_type_marker_object_without_leak`
  - `tests/test_anthropic_provider.py::test_anthropic_provider_rejects_content_type_marker_object_without_leak`
- Initial failures proved non-string marker objects could execute hostile equality hooks raising
  `client_secret=type-marker-secret` before provider output selection failed closed.
- Added 1 failing-first documentation assertion:
  `tests/test_project_docs.py::test_sprint_687_documents_provider_content_type_marker_boundary`
- Initial documentation failure proved this sprint log did not exist yet.

## Changes

- OpenAI nested `output[].content[].type` markers now require exact `str` values before comparison
  with `output_text`.
- Anthropic `content[].type` markers now require exact `str` values before comparison with `text`.
- Non-string marker values are ignored as missing provider output instead of being compared,
  stringified, or surfaced.
- Documented the provider content marker boundary in the operator guide.

## Verification

- `python3 -m pytest tests/test_openai_provider.py::test_openai_responses_provider_rejects_content_type_marker_object_without_leak tests/test_anthropic_provider.py::test_anthropic_provider_rejects_content_type_marker_object_without_leak -q`
  failed first because hostile marker equality hooks executed.
- `python3 -m pytest tests/test_openai_provider.py::test_openai_responses_provider_rejects_content_type_marker_object_without_leak tests/test_anthropic_provider.py::test_anthropic_provider_rejects_content_type_marker_object_without_leak tests/test_openai_provider.py::test_openai_responses_provider_parses_output_item_text tests/test_anthropic_provider.py::test_anthropic_provider_posts_structured_output_request -q`
  passed, 4 tests.
- `python3 -m pytest tests/test_project_docs.py -q -k sprint_687`
  failed first while this changelog was missing.
- `python3 -m pytest tests/test_project_docs.py -q -k sprint_687` passed, 1 test.
- `python3 -m pytest tests/test_openai_provider.py tests/test_anthropic_provider.py -q` passed,
  143 tests.
- `ruff check src tests` passed.
- `mypy src tests` passed across 197 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` passed,
  2927 tests with 93.14% total coverage.
