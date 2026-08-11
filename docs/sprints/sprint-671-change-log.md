# Sprint 671 Change Log

## Provider rationale control-character boundary

Sprint 671 tightened provider change rationale handling. Before this sprint, provider rationale text was exact-string and length bounded, but newline/control-bearing rationale text could enter normalized candidate changes. Rationale is operator-facing audit metadata, so allowing control characters creates avoidable log-shaping and work-note-shaping risk even when diagnostics avoid echoing rejected values.

Provider change `rationale` values may still be `null` or ordinary sentence text up to 2000 characters. Exact string rationale values containing ASCII control characters, including newline and DEL, now fail closed with `<Provider> response change rationale must not contain control characters` before normalized artifacts are returned.

Verification:

- Added 2 failing-first provider-response-normalization assertions proving newline/control-bearing rationale text was accepted before implementation.
- Added 1 positive provider-response-normalization assertion proving ordinary sentence rationale text remains accepted.
- `python3 -m pytest tests/test_provider_response_normalization.py::test_provider_candidate_normalization_rejects_rationale_control_characters_without_leak tests/test_provider_response_normalization.py::test_provider_candidate_normalization_accepts_sentence_rationale -q`: failed before implementation because control-character rationale text was accepted.
- `python3 -m pytest tests/test_provider_response_normalization.py::test_provider_candidate_normalization_rejects_rationale_control_characters_without_leak tests/test_provider_response_normalization.py::test_provider_candidate_normalization_accepts_sentence_rationale -q`: 3 tests passed.
- `ruff check src/jedi_devproject/provider_response_normalization.py tests/test_provider_response_normalization.py`: all checks passed.
- `python3 -m pytest tests/test_project_docs.py::test_sprint_671_documents_provider_rationale_control_character_boundary -q`: failed before documentation because the Sprint 671 change log did not exist.
- `python3 -m pytest tests/test_project_docs.py::test_sprint_671_documents_provider_rationale_control_character_boundary -q`: 1 test passed.
- `python3 -m pytest tests/test_provider_response_normalization.py -q`: 64 tests passed.
- `mypy src/jedi_devproject/provider_response_normalization.py tests/test_provider_response_normalization.py`: success with no issues in 2 source files.
- `python3 -m pytest tests/test_provider_response_normalization.py tests/test_openai_provider.py tests/test_anthropic_provider.py tests/test_provider_contract.py -q`: 185 tests passed.
- `ruff check src tests`: all checks passed.
- `mypy src tests`: success with no issues in 197 source files.
- `python3 -m pytest tests/test_project_docs.py -q`: 745 tests passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2872 tests passed with 93.04% total coverage.
