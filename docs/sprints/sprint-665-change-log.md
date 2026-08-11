# Sprint 665 Change Log

## Provider schema numeric-bound alignment

Sprint 665 continued production hardening by aligning the OpenAI structured-output schema with the numeric safe range enforced by the shared provider normalizer. Sprint 662 added deterministic rejection for provider numeric field values outside `-9007199254740991..9007199254740991`, and Sprint 664 aligned string and collection bounds in the OpenAI schema, but the numeric safe range was still absent from the provider-facing schema.

`implementation_candidate_schema()` now exposes `minimum` and `maximum` on provider field-value schema entries using the same `MAX_PROVIDER_JSON_SAFE_NUMBER_ABS` constant as deterministic validation. OpenAI sees the range during structured output generation; Anthropic still strips unsupported `minimum` and `maximum` constraints before sending and relies on the shared normalizer for enforcement.

Verification:

- Added 1 failing-first OpenAI provider schema assertion proving the numeric safe range was missing from the provider-facing schema.
- `python3 -m pytest tests/test_openai_provider.py::test_openai_responses_provider_posts_structured_output_request -q`: failed before implementation because the provider field-value schema did not include `minimum` and `maximum`.
- `python3 -m pytest tests/test_openai_provider.py::test_openai_responses_provider_posts_structured_output_request -q`: 1 test passed.
- `python3 -m pytest tests/test_anthropic_provider.py::test_anthropic_provider_schema_strips_unsupported_constraints -q`: 1 test passed.
- `python3 -m pytest tests/test_project_docs.py::test_sprint_665_documents_provider_schema_numeric_bound_alignment -q`: failed before documentation because the Sprint 665 change log did not exist.
- `python3 -m pytest tests/test_project_docs.py::test_sprint_665_documents_provider_schema_numeric_bound_alignment -q`: 1 test passed.
- `python3 -m pytest tests/test_provider_response_normalization.py tests/test_anthropic_provider.py tests/test_openai_provider.py -q`: 160 tests passed.
- `ruff check src/jedi_devproject/provider_contract.py tests/test_openai_provider.py tests/test_project_docs.py`: all checks passed.
- `ruff check src tests`: all checks passed.
- `mypy src tests`: success with no issues in 197 source files.
- `python3 -m pytest tests/test_project_docs.py -q`: 739 tests passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2845 tests passed with 93.03% total coverage.
