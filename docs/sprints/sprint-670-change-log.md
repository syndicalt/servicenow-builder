# Sprint 670 Change Log

## Provider identifier pattern single-source enforcement

Sprint 670 removed a schema/runtime drift risk introduced by having two separate safe-identifier implementations. Sprints 667 through 669 established `PROVIDER_SAFE_IDENTIFIER_PATTERN` for provider schemas and added runtime rejection for unsafe table and field identifiers, but runtime normalization still used hand-coded ASCII checks instead of the exported pattern constant. That meant a future schema pattern change could silently diverge from runtime enforcement.

Runtime table and field identifier validation now calls `re.fullmatch(PROVIDER_SAFE_IDENTIFIER_PATTERN, value)`. The OpenAI schema, Anthropic stripping path, and deterministic response normalization all depend on the same exported pattern constant, with downstream validation still returning fixed diagnostics that do not echo rejected identifier values.

Verification:

- Added 2 failing-first provider-response-normalization assertions proving runtime validation ignored the exported pattern before implementation.
- `python3 -m pytest tests/test_provider_response_normalization.py::test_provider_candidate_normalization_uses_exported_identifier_pattern_for_tables tests/test_provider_response_normalization.py::test_provider_candidate_normalization_uses_exported_identifier_pattern_for_fields -q`: failed before implementation because runtime validation ignored the exported pattern.
- `python3 -m pytest tests/test_provider_response_normalization.py::test_provider_candidate_normalization_uses_exported_identifier_pattern_for_tables tests/test_provider_response_normalization.py::test_provider_candidate_normalization_uses_exported_identifier_pattern_for_fields tests/test_provider_response_normalization.py::test_provider_candidate_normalization_rejects_unsafe_field_identifier_without_leak tests/test_provider_response_normalization.py::test_provider_candidate_normalization_accepts_safe_field_identifier tests/test_provider_response_normalization.py::test_provider_candidate_normalization_rejects_unsafe_table_identifier_without_leak tests/test_provider_response_normalization.py::test_provider_candidate_normalization_accepts_safe_table_identifier -q`: 16 tests passed.
- `python3 -m pytest tests/test_project_docs.py::test_sprint_670_documents_provider_identifier_pattern_single_source -q`: failed before documentation because the Sprint 670 change log did not exist.
- `python3 -m pytest tests/test_project_docs.py::test_sprint_670_documents_provider_identifier_pattern_single_source -q`: 1 test passed.
- `python3 -m pytest tests/test_provider_response_normalization.py -q`: 61 tests passed.
- `ruff check src/jedi_devproject/provider_response_normalization.py tests/test_provider_response_normalization.py tests/test_project_docs.py`: all checks passed.
- `mypy src/jedi_devproject/provider_response_normalization.py`: success with no issues in 1 source file.
- `python3 -m pytest tests/test_provider_response_normalization.py tests/test_openai_provider.py tests/test_anthropic_provider.py tests/test_provider_contract.py -q`: 182 tests passed.
- `ruff check src tests`: all checks passed.
- `mypy src tests`: failed once on a missing test variable annotation, then passed after adding explicit candidate annotations.
- `python3 -m pytest tests/test_project_docs.py -q`: 744 tests passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2868 tests passed with 93.04% total coverage.
