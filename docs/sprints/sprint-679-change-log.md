# Sprint 679 Change Log - Provider response list exact-container boundary

## Scope

Hardened model provider response traversal so OpenAI and Anthropic adapters only traverse exact JSON
lists returned by trusted decoding. List subclasses are treated as missing provider output instead of
being iterated while scanning for model JSON text.

## Tests First

- Added 3 failing-first provider response-list assertions:
  - `tests/test_openai_provider.py::test_openai_responses_provider_rejects_output_list_subclass_without_leak`
  - `tests/test_openai_provider.py::test_openai_responses_provider_rejects_content_list_subclass_without_leak`
  - `tests/test_anthropic_provider.py::test_anthropic_provider_rejects_content_list_subclass_without_leak`
- Initial failures proved hostile response-list subclasses could execute iterators raising
  `client_secret=output-list-secret` and `client_secret=content-list-secret` before provider errors
  were raised.
- Added 1 failing-first documentation assertion:
  `tests/test_project_docs.py::test_sprint_679_documents_provider_response_list_exact_container_boundary`
- Initial documentation failure proved this sprint log did not exist yet.

## Changes

- OpenAI fallback `output` traversal now requires `type(output) is list`.
- OpenAI nested `content` traversal now requires exact `list`.
- Anthropic successful-response `content` traversal now requires exact `list`.
- Documented exact-list model response container parsing for both provider adapters.

## Verification

- `python3 -m pytest tests/test_openai_provider.py::test_openai_responses_provider_rejects_output_list_subclass_without_leak tests/test_openai_provider.py::test_openai_responses_provider_rejects_content_list_subclass_without_leak tests/test_anthropic_provider.py::test_anthropic_provider_rejects_content_list_subclass_without_leak -q`
  failed first because provider parsing executed hostile list-subclass iterators and surfaced
  `client_secret=output-list-secret` and `client_secret=content-list-secret`.
- `python3 -m pytest tests/test_openai_provider.py::test_openai_responses_provider_rejects_output_list_subclass_without_leak tests/test_openai_provider.py::test_openai_responses_provider_rejects_content_list_subclass_without_leak tests/test_openai_provider.py::test_openai_responses_provider_does_not_scan_unbounded_output_items tests/test_openai_provider.py::test_openai_responses_provider_does_not_scan_unbounded_content_items tests/test_anthropic_provider.py::test_anthropic_provider_rejects_content_list_subclass_without_leak tests/test_anthropic_provider.py::test_anthropic_provider_does_not_scan_unbounded_content_blocks -q`
  passed, 6 tests.
- `python3 -m pytest tests/test_project_docs.py::test_sprint_679_documents_provider_response_list_exact_container_boundary -q`
  failed first while this changelog was missing.
- `python3 -m pytest tests/test_openai_provider.py::test_openai_responses_provider_rejects_output_list_subclass_without_leak tests/test_openai_provider.py::test_openai_responses_provider_rejects_content_list_subclass_without_leak tests/test_anthropic_provider.py::test_anthropic_provider_rejects_content_list_subclass_without_leak tests/test_project_docs.py::test_sprint_679_documents_provider_response_list_exact_container_boundary -q`
  passed, 4 tests.
- `ruff check src/jedi_devproject/openai_provider.py src/jedi_devproject/anthropic_provider.py tests/test_openai_provider.py tests/test_anthropic_provider.py tests/test_project_docs.py`
  passed.
- `mypy src/jedi_devproject/openai_provider.py src/jedi_devproject/anthropic_provider.py tests/test_openai_provider.py tests/test_anthropic_provider.py`
  passed across 4 source files.
- `python3 -m pytest tests/test_openai_provider.py tests/test_anthropic_provider.py -q` passed, 124 tests.
- `python3 -m pytest tests/test_project_docs.py -q` passed, 753 tests.
- `ruff check src tests` passed.
- `mypy src tests` passed across 197 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` passed,
  2896 tests with 93.07% total coverage.
