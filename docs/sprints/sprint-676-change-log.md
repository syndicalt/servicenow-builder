# Sprint 676 Change Log - Provider prompt sentence-boundary hardening

## Scope

Hardened the shared provider system prompt so adjacent Python string literals cannot collapse Business
Rule guidance and Catalog Item guidance into one malformed sentence.

## Tests First

- Added 1 failing-first provider-contract assertion:
  `tests/test_provider_contract.py::test_implementation_system_prompt_has_sentence_boundary_before_catalog_guidance`
- Initial failure proved the existing prompt contained `script.For standard Catalog`.
- Added 1 failing-first documentation assertion:
  `tests/test_project_docs.py::test_sprint_676_documents_provider_prompt_sentence_boundary`
- Initial documentation failure proved this sprint log did not exist yet.

## Changes

- Fixed `IMPLEMENTATION_SYSTEM_PROMPT` so the executable-script sentence ends as
  `script. For standard Catalog Item builds`.
- Documented the prompt boundary in the operator guide because both OpenAI and Anthropic adapters send
  the shared prompt verbatim.

## Verification

- `python3 -m pytest tests/test_provider_contract.py::test_implementation_system_prompt_has_sentence_boundary_before_catalog_guidance -q`
  failed first on the existing `script.For standard Catalog` prompt boundary.
- `python3 -m pytest tests/test_project_docs.py::test_sprint_676_documents_provider_prompt_sentence_boundary -q`
  failed first while this changelog was missing.
- `python3 -m pytest tests/test_provider_contract.py::test_implementation_system_prompt_has_sentence_boundary_before_catalog_guidance tests/test_provider_contract.py::test_both_adapters_send_the_shared_system_prompt tests/test_project_docs.py::test_sprint_676_documents_provider_prompt_sentence_boundary -q`
  passed, 3 tests.
- `python3 -m pytest tests/test_provider_contract.py tests/test_openai_provider.py tests/test_anthropic_provider.py -q`
  passed, 122 tests.
- `ruff check src tests` passed.
- `mypy src tests` passed across 197 source files.
- `python3 -m pytest tests/test_project_docs.py -q` passed, 750 tests.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` passed,
  2886 tests with 93.05% total coverage.
