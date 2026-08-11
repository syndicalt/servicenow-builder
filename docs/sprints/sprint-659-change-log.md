# Sprint 659 Change Log

## Provider root text-list bound normalization boundary

Sprint 659 continued production hardening by bounding root-level provider `test_plan` and `rollback_notes` lists after JSON parsing. Earlier sprints required exact lists with exact string items, but a model response could still submit very large note lists or oversized note strings and carry them into artifacts, diagnostics, or downstream validation.

Provider `test_plan` and `rollback_notes` now allow at most 100 items per list and at most 2000 characters per item. Oversized lists fail closed with `<Provider> response <field> includes too many items (max 100)`. Oversized note items fail closed with `<Provider> response <field> item exceeds 2000 characters`. Diagnostics do not echo model-provided note text or exception text.

Verification:

- Added 2 failing-first provider-response-normalization tests proving oversized root text-list counts and oversized note items were accepted before implementation.
- `python3 -m pytest tests/test_provider_response_normalization.py::test_provider_candidate_normalization_rejects_too_many_test_plan_items_without_leak tests/test_provider_response_normalization.py::test_provider_candidate_normalization_rejects_oversized_rollback_note_without_leak -q`: failed before implementation because oversized root note data was accepted.
- `python3 -m pytest tests/test_provider_response_normalization.py tests/test_anthropic_provider.py tests/test_openai_provider.py -q`: 148 tests passed.
- `ruff check src/jedi_devproject/provider_response_normalization.py tests/test_provider_response_normalization.py tests/test_anthropic_provider.py tests/test_openai_provider.py`: all checks passed.
- `ruff check src tests`: all checks passed.
- `mypy src tests`: success with no issues in 197 source files.
- `python3 -m pytest tests/test_project_docs.py -q`: 733 tests passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2827 tests passed with 93.01% total coverage.
