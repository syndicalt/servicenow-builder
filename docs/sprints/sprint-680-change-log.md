# Sprint 680 Change Log - Provider response dict exact-item boundary

## Scope

Hardened model provider response lookup so OpenAI and Anthropic adapters only inspect exact JSON
dictionaries while selecting model output text. Dictionary subclasses are treated as missing provider
output instead of being queried during response traversal.

## Tests First

- Added 3 failing-first provider response-dict assertions:
  - `tests/test_openai_provider.py::test_openai_responses_provider_rejects_output_item_dict_subclass_without_leak`
  - `tests/test_openai_provider.py::test_openai_responses_provider_rejects_content_item_dict_subclass_without_leak`
  - `tests/test_anthropic_provider.py::test_anthropic_provider_rejects_content_block_dict_subclass_without_leak`
- Initial failures proved hostile response dictionary subclasses could execute lookup hooks raising
  `client_secret=output-item-secret`, `client_secret=content-item-secret`, and
  `client_secret=content-block-secret` before provider errors were raised.
- Added 1 failing-first documentation assertion:
  `tests/test_project_docs.py::test_sprint_680_documents_provider_response_dict_exact_item_boundary`
- Initial documentation failure proved this sprint log did not exist yet.

## Changes

- OpenAI fallback `output` item traversal now requires exact `dict` items before reading `content`.
- OpenAI nested `content` item traversal now requires exact `dict` items before reading `text`.
- Anthropic successful-response `content` block traversal now requires exact `dict` blocks before
  reading `text`.
- Documented exact-dictionary model response item parsing for both provider adapters.

## Verification

- `python3 -m pytest tests/test_openai_provider.py::test_openai_responses_provider_rejects_output_item_dict_subclass_without_leak tests/test_openai_provider.py::test_openai_responses_provider_rejects_content_item_dict_subclass_without_leak tests/test_anthropic_provider.py::test_anthropic_provider_rejects_content_block_dict_subclass_without_leak -q`
  failed first because provider parsing executed hostile dictionary-subclass lookup hooks and surfaced
  `client_secret=output-item-secret`, `client_secret=content-item-secret`, and
  `client_secret=content-block-secret`.
- `python3 -m pytest tests/test_openai_provider.py::test_openai_responses_provider_rejects_output_item_dict_subclass_without_leak tests/test_openai_provider.py::test_openai_responses_provider_rejects_content_item_dict_subclass_without_leak tests/test_openai_provider.py::test_openai_responses_provider_posts_structured_output_request tests/test_anthropic_provider.py::test_anthropic_provider_rejects_content_block_dict_subclass_without_leak tests/test_anthropic_provider.py::test_anthropic_provider_posts_structured_output_request -q`
  passed, 5 tests.
- `python3 -m pytest tests/test_project_docs.py::test_sprint_680_documents_provider_response_dict_exact_item_boundary -q`
  failed first while this changelog was missing.
- `python3 -m pytest tests/test_openai_provider.py::test_openai_responses_provider_rejects_output_item_dict_subclass_without_leak tests/test_openai_provider.py::test_openai_responses_provider_rejects_content_item_dict_subclass_without_leak tests/test_anthropic_provider.py::test_anthropic_provider_rejects_content_block_dict_subclass_without_leak tests/test_project_docs.py::test_sprint_680_documents_provider_response_dict_exact_item_boundary -q`
  passed, 4 tests.
- `ruff check src/jedi_devproject/openai_provider.py src/jedi_devproject/anthropic_provider.py tests/test_openai_provider.py tests/test_anthropic_provider.py tests/test_project_docs.py`
  passed.
- `mypy src/jedi_devproject/openai_provider.py src/jedi_devproject/anthropic_provider.py tests/test_openai_provider.py tests/test_anthropic_provider.py`
  passed across 4 source files.
- `python3 -m pytest tests/test_openai_provider.py tests/test_anthropic_provider.py -q` passed, 127 tests.
- `python3 -m pytest tests/test_project_docs.py -q` passed, 754 tests.
- `ruff check src tests` passed.
- `mypy src tests` passed across 197 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` passed,
  2900 tests with 93.09% total coverage.
