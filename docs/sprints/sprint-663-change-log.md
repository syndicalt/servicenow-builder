# Sprint 663 Change Log

## Provider minimum-change normalization boundary

Sprint 663 continued production hardening by aligning the shared provider normalizer with the model-facing implementation-candidate schema. The OpenAI JSON schema already requires `changes` to contain at least one item, but the deterministic normalizer accepted empty provider change lists. Anthropic strips unsupported schema constraints, so this invariant must live in shared validation rather than relying only on provider-side schema enforcement.

Provider candidates now fail closed with `<Provider> response must include at least one change` when `changes` is an empty exact list. The check runs after root `test_plan` and `rollback_notes` validation, preserving existing diagnostics for malformed root text-list shapes.

Verification:

- Added 1 failing-first provider-response-normalization test proving empty provider change lists were accepted before implementation.
- `python3 -m pytest tests/test_provider_response_normalization.py::test_provider_candidate_normalization_rejects_empty_changes -q`: failed before implementation because empty provider change lists were accepted.
- `python3 -m pytest tests/test_provider_response_normalization.py::test_provider_candidate_normalization_rejects_empty_changes -q`: 1 test passed.
- Updated `tests/test_openai_provider.py::test_openai_responses_provider_parses_output_item_text` to use a valid minimum candidate shape instead of an invalid empty change list.
- `python3 -m pytest tests/test_provider_response_normalization.py::test_provider_candidate_normalization_rejects_empty_changes tests/test_openai_provider.py::test_openai_responses_provider_parses_output_item_text -q`: 2 tests passed.
- `python3 -m pytest tests/test_provider_response_normalization.py tests/test_anthropic_provider.py tests/test_openai_provider.py -q`: 160 tests passed.
- `python3 -m pytest tests/test_project_docs.py::test_sprint_663_documents_provider_minimum_change_count -q`: failed before documentation because the Sprint 663 change log did not exist.
- `python3 -m pytest tests/test_project_docs.py::test_sprint_663_documents_provider_minimum_change_count -q`: 1 test passed.
- `ruff check src/jedi_devproject/provider_response_normalization.py tests/test_provider_response_normalization.py tests/test_openai_provider.py tests/test_anthropic_provider.py tests/test_project_docs.py`: all checks passed.
- `ruff check src tests`: all checks passed.
- `mypy src tests`: failed once on an untyped OpenAI fixture expectation, then passed after making the expected normalized candidate explicit.
- `python3 -m pytest tests/test_project_docs.py -q`: 737 tests passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2843 tests passed with 93.03% total coverage.
