# Sprint 672 Change Log

## Provider review-list control-character boundary

Sprint 672 hardened root provider review-list text after Sprint 671 closed the same class of issue for change rationale metadata. Before this sprint, `test_plan` and `rollback_notes` items were exact-string, non-empty, count-bounded, and length-bounded, but newline/control-bearing review-list text could still enter normalized provider candidates. These items are operator-facing evidence and can flow into artifacts or work-note planning, so raw control characters are not an acceptable production boundary.

Root provider review-list items may still be ordinary sentence text up to 2000 characters. Items containing ASCII control characters, including newline and DEL, now fail closed with `<Provider> response <list> items must not contain control characters` before normalized artifacts are returned.

Verification:

- Added 2 failing-first provider-response-normalization assertions proving newline/control-bearing review-list text was accepted before implementation.
- Added 2 positive provider-response-normalization assertions proving ordinary sentence review-list items remain accepted.
- `python3 -m pytest tests/test_provider_response_normalization.py::test_provider_candidate_normalization_rejects_root_text_item_control_characters_without_leak tests/test_provider_response_normalization.py::test_provider_candidate_normalization_accepts_sentence_root_text_item -q`: failed before implementation because control-character review-list text was accepted.
- `python3 -m pytest tests/test_provider_response_normalization.py::test_provider_candidate_normalization_rejects_root_text_item_control_characters_without_leak tests/test_provider_response_normalization.py::test_provider_candidate_normalization_accepts_sentence_root_text_item -q`: 4 tests passed.
- `ruff check src/jedi_devproject/provider_response_normalization.py tests/test_provider_response_normalization.py`: all checks passed.
- `python3 -m pytest tests/test_project_docs.py::test_sprint_672_documents_provider_review_list_control_character_boundary -q`: failed before documentation because the Sprint 672 change log did not exist.
- `python3 -m pytest tests/test_project_docs.py::test_sprint_672_documents_provider_review_list_control_character_boundary -q`: 1 test passed.
- `python3 -m pytest tests/test_provider_response_normalization.py -q`: 68 tests passed.
- `mypy src/jedi_devproject/provider_response_normalization.py tests/test_provider_response_normalization.py`: success with no issues in 2 source files.
- `python3 -m pytest tests/test_provider_response_normalization.py tests/test_openai_provider.py tests/test_anthropic_provider.py tests/test_provider_contract.py -q`: 189 tests passed.
- `ruff check src tests`: all checks passed.
- `mypy src tests`: success with no issues in 197 source files.
- `python3 -m pytest tests/test_project_docs.py -q`: 746 tests passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2877 tests passed with 93.04% total coverage.
