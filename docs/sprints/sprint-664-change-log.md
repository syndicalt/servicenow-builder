# Sprint 664 Change Log

## Provider schema bound alignment

Sprint 664 continued production hardening by aligning the OpenAI structured-output schema with the shared provider normalizer bounds. Earlier sprints added deterministic limits for candidate changes, change fields, table names, field names, string field values, rationale text, and root review lists, but the OpenAI schema only advertised `changes.minItems`. That schema drift allowed the model to be prompted with a looser contract than the one the deterministic validator enforced.

`implementation_candidate_schema()` now imports the authoritative provider-response normalizer constants and exposes matching JSON Schema bounds where supported: `changes.maxItems`, change `fields.maxItems`, table and field-name `maxLength`, field string-value `maxLength`, rationale `maxLength`, and root `test_plan`/`rollback_notes` item-count and item-length caps. Anthropic continues to strip unsupported schema constraints before sending its schema, so deterministic normalization remains the enforcement boundary there.

Verification:

- Added 1 failing-first OpenAI provider schema test proving schema drift between provider prompts and deterministic provider-response validation.
- `python3 -m pytest tests/test_openai_provider.py::test_openai_responses_provider_posts_structured_output_request -q`: failed before implementation because provider-response bounds were missing from the OpenAI schema.
- `python3 -m pytest tests/test_openai_provider.py::test_openai_responses_provider_posts_structured_output_request -q`: 1 test passed.
- `python3 -m pytest tests/test_anthropic_provider.py::test_anthropic_provider_schema_strips_unsupported_constraints -q`: 1 test passed.
- `python3 -m pytest tests/test_project_docs.py::test_sprint_664_documents_provider_schema_bound_alignment -q`: failed before documentation because the Sprint 664 change log did not exist.
- `python3 -m pytest tests/test_project_docs.py::test_sprint_664_documents_provider_schema_bound_alignment -q`: failed once on wording, then passed after the operator-guide note matched the documented Anthropic constraint-stripping boundary.
- `python3 -m pytest tests/test_provider_response_normalization.py tests/test_anthropic_provider.py tests/test_openai_provider.py -q`: 160 tests passed.
- `ruff check src/jedi_devproject/provider_contract.py src/jedi_devproject/provider_response_normalization.py tests/test_provider_response_normalization.py tests/test_openai_provider.py tests/test_anthropic_provider.py tests/test_project_docs.py`: all checks passed.
- `ruff check src tests`: all checks passed.
- `mypy src tests`: success with no issues in 197 source files.
- `python3 -m pytest tests/test_project_docs.py -q`: 738 tests passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2844 tests passed with 93.03% total coverage.
