# Sprint 666 Change Log

## Provider review-list item non-empty boundary

Sprint 666 continued production hardening by rejecting blank provider review-list items. Earlier sprints required root `test_plan` and `rollback_notes` values to be exact lists of exact strings with bounded counts and item lengths, but empty or whitespace-only strings could still enter normalized candidates, artifacts, and audit notes.

Provider root review-list items now must be non-empty exact strings after trimming whitespace. Blank provider review-list items fail closed with diagnostics such as `<Provider> response test_plan items must be non-empty exact strings` and `<Provider> response rollback_notes items must be non-empty exact strings`. Empty lists remain allowed for current callers; the hardening applies to items when present. The OpenAI structured-output schema now advertises `minLength: 1` for both review-list item types, while Anthropic still strips unsupported length constraints and relies on deterministic normalization.

Verification:

- Added 2 failing-first provider-response-normalization assertions proving blank provider review-list items were accepted before implementation.
- Added failing-first OpenAI provider schema assertions proving review-list item `minLength` constraints were missing from the provider-facing schema.
- `python3 -m pytest tests/test_provider_response_normalization.py::test_provider_candidate_normalization_rejects_empty_root_text_item -q`: failed before implementation because blank provider review-list items were accepted.
- `python3 -m pytest tests/test_openai_provider.py::test_openai_responses_provider_posts_structured_output_request -q`: failed before implementation because review-list item `minLength` constraints were missing from the OpenAI schema.
- `python3 -m pytest tests/test_provider_response_normalization.py::test_provider_candidate_normalization_rejects_empty_root_text_item -q`: 2 tests passed.
- `python3 -m pytest tests/test_openai_provider.py::test_openai_responses_provider_posts_structured_output_request -q`: 1 test passed.
- `python3 -m pytest tests/test_anthropic_provider.py::test_anthropic_provider_schema_strips_unsupported_constraints -q`: 1 test passed.
- `python3 -m pytest tests/test_project_docs.py::test_sprint_666_documents_provider_review_item_non_empty_boundary -q`: failed before documentation because the Sprint 666 change log did not exist.
- `python3 -m pytest tests/test_project_docs.py::test_sprint_666_documents_provider_review_item_non_empty_boundary -q`: 1 test passed.
- `python3 -m pytest tests/test_provider_response_normalization.py tests/test_anthropic_provider.py tests/test_openai_provider.py -q`: 162 tests passed.
- `ruff check src/jedi_devproject/provider_response_normalization.py src/jedi_devproject/provider_contract.py tests/test_provider_response_normalization.py tests/test_openai_provider.py tests/test_project_docs.py`: all checks passed.
- `ruff check src tests`: all checks passed.
- `mypy src tests`: success with no issues in 197 source files.
- `python3 -m pytest tests/test_project_docs.py -q`: 740 tests passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2848 tests passed with 93.03% total coverage.
