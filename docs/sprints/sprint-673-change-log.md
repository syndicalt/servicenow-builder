# Sprint 673 Change Log

## Provider schema no-control text-pattern alignment

Sprint 673 aligned the OpenAI structured-output schema with the control-character text boundaries added in Sprints 671 and 672. Runtime normalization already rejected ASCII control characters in provider change rationale text and root review-list items, but the model-facing OpenAI schema only advertised length and count bounds. That left the model unguided on a deterministic post-generation rejection boundary.

The shared implementation-candidate schema now advertises `^[^\u0000-\u001F\u007F]*$` for provider change `rationale`, `test_plan` items, and `rollback_notes` items. Anthropic structured outputs continue to strip unsupported `pattern` constraints before sending the schema; deterministic normalization remains authoritative for both providers and offline provider response validation.

Verification:

- Added 1 failing-first OpenAI provider schema assertion proving the no-control text pattern was missing from the transmitted schema before implementation.
- Kept the Anthropic schema-stripping assertion proving `pattern` constraints are not sent to Anthropic structured outputs.
- `python3 -m pytest tests/test_openai_provider.py::test_openai_responses_provider_posts_structured_output_request tests/test_anthropic_provider.py::test_anthropic_provider_schema_strips_unsupported_constraints -q`: failed before implementation because the rationale schema lacked `pattern`.
- `python3 -m pytest tests/test_openai_provider.py::test_openai_responses_provider_posts_structured_output_request tests/test_anthropic_provider.py::test_anthropic_provider_schema_strips_unsupported_constraints -q`: 2 tests passed.
- `python3 -m pytest tests/test_project_docs.py::test_sprint_673_documents_provider_schema_no_control_text_pattern_alignment -q`: failed before documentation because the Sprint 673 change log did not exist.
- `python3 -m pytest tests/test_project_docs.py::test_sprint_673_documents_provider_schema_no_control_text_pattern_alignment -q`: 1 test passed.
- `python3 -m pytest tests/test_openai_provider.py::test_openai_responses_provider_posts_structured_output_request tests/test_anthropic_provider.py::test_anthropic_provider_schema_strips_unsupported_constraints tests/test_provider_response_normalization.py::test_provider_candidate_normalization_rejects_rationale_control_characters_without_leak tests/test_provider_response_normalization.py::test_provider_candidate_normalization_rejects_root_text_item_control_characters_without_leak -q`: 6 tests passed.
- `ruff check src/jedi_devproject/provider_response_normalization.py src/jedi_devproject/provider_contract.py tests/test_openai_provider.py tests/test_project_docs.py`: all checks passed.
- `mypy src/jedi_devproject/provider_response_normalization.py src/jedi_devproject/provider_contract.py`: success with no issues in 2 source files.
- `python3 -m pytest tests/test_provider_response_normalization.py tests/test_openai_provider.py tests/test_anthropic_provider.py tests/test_provider_contract.py -q`: 189 tests passed.
- `ruff check src tests`: all checks passed.
- `mypy src tests`: success with no issues in 197 source files.
- `python3 -m pytest tests/test_project_docs.py -q`: 747 tests passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2878 tests passed with 93.04% total coverage.
