# Sprint 674 Change Log

## Provider text pattern single-source enforcement

Sprint 674 removed the schema/runtime drift risk left after Sprint 673 introduced `PROVIDER_NO_CONTROL_TEXT_PATTERN` for model-facing schema guidance. Runtime rationale and review-list validation still used separate hand-coded control-character checks, so a future update to the exported text policy could silently diverge from deterministic enforcement.

Runtime provider text validation now calls `re.fullmatch(PROVIDER_NO_CONTROL_TEXT_PATTERN, value)` for change rationale text and root review-list items. The default control-character diagnostics remain stable for newline, DEL, and other ASCII control characters. If the exported text policy is intentionally tightened later, runtime validation fails closed with fixed text-policy diagnostics without echoing rejected rationale or review-list values.

Verification:

- Added 2 failing-first provider-response-normalization assertions proving runtime text validation ignored the exported pattern before implementation.
- `python3 -m pytest tests/test_provider_response_normalization.py::test_provider_candidate_normalization_uses_exported_text_pattern_for_root_text_items tests/test_provider_response_normalization.py::test_provider_candidate_normalization_uses_exported_text_pattern_for_rationale -q`: failed before implementation because runtime validation ignored the exported pattern.
- `python3 -m pytest tests/test_provider_response_normalization.py::test_provider_candidate_normalization_uses_exported_text_pattern_for_root_text_items tests/test_provider_response_normalization.py::test_provider_candidate_normalization_uses_exported_text_pattern_for_rationale tests/test_provider_response_normalization.py::test_provider_candidate_normalization_rejects_root_text_item_control_characters_without_leak tests/test_provider_response_normalization.py::test_provider_candidate_normalization_rejects_rationale_control_characters_without_leak -q`: 6 tests passed.
- `python3 -m pytest tests/test_project_docs.py::test_sprint_674_documents_provider_text_pattern_single_source -q`: failed before documentation because the Sprint 674 change log did not exist.
- `python3 -m pytest tests/test_project_docs.py::test_sprint_674_documents_provider_text_pattern_single_source -q`: 1 test passed.
- `python3 -m pytest tests/test_provider_response_normalization.py -q`: 70 tests passed.
- `ruff check src/jedi_devproject/provider_response_normalization.py tests/test_provider_response_normalization.py tests/test_project_docs.py`: all checks passed.
- `mypy src/jedi_devproject/provider_response_normalization.py tests/test_provider_response_normalization.py`: success with no issues in 2 source files.
- `python3 -m pytest tests/test_provider_response_normalization.py tests/test_openai_provider.py tests/test_anthropic_provider.py tests/test_provider_contract.py -q`: 191 tests passed.
- `ruff check src tests`: all checks passed.
- `mypy src tests`: success with no issues in 197 source files.
- `python3 -m pytest tests/test_project_docs.py -q`: 748 tests passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2881 tests passed with 93.05% total coverage.
