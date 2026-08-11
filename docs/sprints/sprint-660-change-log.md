# Sprint 660 Change Log

## Provider change metadata text-bound normalization boundary

Sprint 660 continued production hardening by bounding provider-generated change metadata after field normalization. Earlier sprints required exact-string `table` and exact-string-or-null `rationale` values, but a model response could still submit blank table identifiers, whitespace/control-bearing table identifiers, oversized table names, or oversized rationale text into candidate artifacts and downstream diagnostics.

Provider change `table` values now fail closed unless they are non-empty exact strings, contain no whitespace or control characters, and contain at most 200 characters. Provider change `rationale` values still allow null or exact strings, but exact strings are capped at 2000 characters. Rejections use fixed diagnostics such as `<Provider> response change table must be a non-empty identifier`, `<Provider> response change table must not contain whitespace or control characters`, `<Provider> response change table exceeds 200 characters`, and `<Provider> response change rationale exceeds 2000 characters` without echoing model-provided metadata.

Verification:

- Added 5 failing-first provider-response-normalization tests proving unsafe table identifiers and oversized rationale text were accepted before implementation.
- `python3 -m pytest tests/test_provider_response_normalization.py::test_provider_candidate_normalization_rejects_blank_change_table_without_leak tests/test_provider_response_normalization.py::test_provider_candidate_normalization_rejects_unsafe_change_table_without_leak tests/test_provider_response_normalization.py::test_provider_candidate_normalization_rejects_oversized_change_table_without_leak tests/test_provider_response_normalization.py::test_provider_candidate_normalization_rejects_oversized_rationale_without_leak -q`: failed before implementation because unsafe change metadata text was accepted.
- `python3 -m pytest tests/test_provider_response_normalization.py::test_provider_candidate_normalization_rejects_blank_change_table_without_leak tests/test_provider_response_normalization.py::test_provider_candidate_normalization_rejects_unsafe_change_table_without_leak tests/test_provider_response_normalization.py::test_provider_candidate_normalization_rejects_oversized_change_table_without_leak tests/test_provider_response_normalization.py::test_provider_candidate_normalization_rejects_oversized_rationale_without_leak -q`: 5 tests passed.
- `python3 -m pytest tests/test_project_docs.py::test_sprint_660_documents_provider_change_metadata_text_bounds -q`: failed before documentation because the Sprint 660 change log did not exist.
- `python3 -m pytest tests/test_project_docs.py::test_sprint_660_documents_provider_change_metadata_text_bounds -q`: 1 test passed.
- `python3 -m pytest tests/test_provider_response_normalization.py tests/test_anthropic_provider.py tests/test_openai_provider.py -q`: 153 tests passed.
- `ruff check src/jedi_devproject/provider_response_normalization.py tests/test_provider_response_normalization.py tests/test_anthropic_provider.py tests/test_openai_provider.py tests/test_project_docs.py`: all checks passed.
- `ruff check src tests`: all checks passed.
- `mypy src tests`: success with no issues in 197 source files.
- `python3 -m pytest tests/test_project_docs.py -q`: 734 tests passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2833 tests passed with 93.02% total coverage.
