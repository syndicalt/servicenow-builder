# Sprint 675 Change Log

## Provider meaningful text-policy boundary

Sprint 675 tightened the shared provider text policy from "no ASCII control characters" to "no ASCII control characters and at least one non-whitespace, non-control character." Before this sprint, runtime normalization rejected blank root review-list items, but blank rationale text such as `""` or `"   "` was accepted even though `null` already represents absent rationale. The OpenAI structured-output schema also advertised only the old no-control pattern.

`PROVIDER_NO_CONTROL_TEXT_PATTERN` now requires meaningful text whenever a provider emits an optional text string. Change rationale may still be `null`; if it is a string, it must contain at least one non-whitespace, non-control character. Root review-list items continue to use the same shared pattern and retain their existing non-empty diagnostics for blank items.

Verification:

- Added 2 failing-first provider-response-normalization assertions proving blank rationale text was accepted before implementation.
- Updated 1 failing-first OpenAI provider schema assertion proving the transmitted schema still advertised the old no-control-only pattern before implementation.
- `python3 -m pytest tests/test_openai_provider.py::test_openai_responses_provider_posts_structured_output_request tests/test_provider_response_normalization.py::test_provider_candidate_normalization_rejects_blank_rationale_without_leak -q`: failed before implementation because the schema used the old pattern and blank rationale text was accepted.
- `python3 -m pytest tests/test_openai_provider.py::test_openai_responses_provider_posts_structured_output_request tests/test_provider_response_normalization.py::test_provider_candidate_normalization_rejects_blank_rationale_without_leak tests/test_provider_response_normalization.py::test_provider_candidate_normalization_accepts_sentence_rationale tests/test_provider_response_normalization.py::test_provider_candidate_normalization_accepts_sentence_root_text_item tests/test_provider_response_normalization.py::test_provider_candidate_normalization_rejects_rationale_control_characters_without_leak tests/test_provider_response_normalization.py::test_provider_candidate_normalization_rejects_root_text_item_control_characters_without_leak -q`: 10 tests passed.
- `ruff check src/jedi_devproject/provider_response_normalization.py tests/test_provider_response_normalization.py tests/test_openai_provider.py`: all checks passed.
- `mypy src/jedi_devproject/provider_response_normalization.py tests/test_provider_response_normalization.py`: success with no issues in 2 source files.
- `python3 -m pytest tests/test_project_docs.py::test_sprint_675_documents_provider_meaningful_text_policy -q`: failed before documentation because the Sprint 675 change log did not exist.
- `python3 -m pytest tests/test_project_docs.py::test_sprint_675_documents_provider_meaningful_text_policy -q`: 1 test passed.
- `python3 -m pytest tests/test_provider_response_normalization.py -q`: 72 tests passed.
- `python3 -m pytest tests/test_openai_provider.py::test_openai_responses_provider_posts_structured_output_request tests/test_anthropic_provider.py::test_anthropic_provider_schema_strips_unsupported_constraints -q`: 2 tests passed.
- `mypy src/jedi_devproject/provider_response_normalization.py src/jedi_devproject/provider_contract.py tests/test_provider_response_normalization.py`: success with no issues in 3 source files.
- `python3 -m pytest tests/test_provider_response_normalization.py tests/test_openai_provider.py tests/test_anthropic_provider.py tests/test_provider_contract.py -q`: 193 tests passed.
- `ruff check src tests`: all checks passed.
- `mypy src tests`: success with no issues in 197 source files.
- `python3 -m pytest tests/test_project_docs.py -q`: 749 tests passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2884 tests passed with 93.05% total coverage.
