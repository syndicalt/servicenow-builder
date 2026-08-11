# Sprint 669 Change Log

## Provider schema identifier-pattern alignment

Sprint 669 aligned the model-facing provider schema with the deterministic safe identifier boundary added in Sprints 667 and 668. Runtime normalization already rejected punctuation-bearing, dotted, digit-leading, and secret-bearing table or field identifiers, but the OpenAI structured-output schema only advertised length bounds. That meant the model was not being guided toward the same ServiceNow-safe identifier shape that the deterministic validator enforced after generation.

The shared implementation-candidate schema now advertises `^[A-Za-z_][A-Za-z0-9_]*$` for provider change `table` values and field-entry `name` values. The same pattern constant is imported from provider response normalization so the schema and runtime boundary stay intentionally linked. Anthropic structured outputs continue to strip unsupported constraints, now including `pattern`, before sending the schema; deterministic normalization remains the authoritative enforcement layer for both adapters.

Verification:

- Added 1 failing-first OpenAI provider schema assertion proving the safe identifier pattern was missing from the transmitted schema before implementation.
- Updated the Anthropic schema-stripping assertion to prove unsupported `pattern` constraints are not sent to Anthropic structured outputs.
- `python3 -m pytest tests/test_openai_provider.py::test_openai_responses_provider_posts_structured_output_request tests/test_anthropic_provider.py::test_anthropic_provider_schema_strips_unsupported_constraints -q`: first attempted with an outdated OpenAI test name and ran no tests; rerun with the correct test failed before implementation because the table schema lacked `pattern`.
- `python3 -m pytest tests/test_openai_provider.py::test_openai_responses_provider_posts_structured_output_request tests/test_anthropic_provider.py::test_anthropic_provider_schema_strips_unsupported_constraints -q`: 2 tests passed.
- `python3 -m pytest tests/test_project_docs.py::test_sprint_669_documents_provider_schema_identifier_pattern_alignment -q`: failed before documentation because the Sprint 669 change log did not exist.
- `python3 -m pytest tests/test_project_docs.py::test_sprint_669_documents_provider_schema_identifier_pattern_alignment -q`: 1 test passed.
- `python3 -m pytest tests/test_openai_provider.py::test_openai_responses_provider_posts_structured_output_request tests/test_anthropic_provider.py::test_anthropic_provider_schema_strips_unsupported_constraints tests/test_provider_response_normalization.py::test_provider_candidate_normalization_rejects_unsafe_field_identifier_without_leak tests/test_provider_response_normalization.py::test_provider_candidate_normalization_rejects_unsafe_table_identifier_without_leak -q`: 10 tests passed.
- `ruff check src/jedi_devproject/provider_response_normalization.py src/jedi_devproject/provider_contract.py src/jedi_devproject/anthropic_provider.py tests/test_openai_provider.py tests/test_anthropic_provider.py tests/test_project_docs.py`: all checks passed.
- `python3 -m pytest tests/test_provider_response_normalization.py tests/test_openai_provider.py tests/test_anthropic_provider.py -q`: 176 tests passed.
- `mypy src/jedi_devproject/provider_response_normalization.py src/jedi_devproject/provider_contract.py src/jedi_devproject/anthropic_provider.py`: success with no issues in 3 source files.
- `ruff check src tests`: all checks passed.
- `mypy src tests`: success with no issues in 197 source files.
- `python3 -m pytest tests/test_project_docs.py -q`: 743 tests passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2865 tests passed with 93.04% total coverage.
