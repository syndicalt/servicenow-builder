# Sprint 656 Change Log

## Provider root text-list normalization boundary

Sprint 656 continued production hardening by tightening shared provider candidate normalization around root-level `test_plan` and `rollback_notes`. The provider schema requires both fields to be arrays of strings, but the normalizer previously returned them untouched. Malformed in-process provider responses could carry missing root note fields, list subclasses, string-subclass note items, or non-string note items past the provider boundary.

Provider `test_plan` and `rollback_notes` are now validated after change normalization, preserving specific change-level diagnostics for malformed `changes` while still failing closed before the normalized candidate is returned. Both fields must be exact lists, and every item must be an exact string. Missing fields, list subclasses, and non-list values fail closed with `<Provider> response test_plan must be an exact list` or `<Provider> response rollback_notes must be an exact list`. String-subclass items and non-string items fail closed with `<Provider> response test_plan items must be exact strings` or `<Provider> response rollback_notes items must be exact strings`. Diagnostics do not echo model-provided note text or exception text.

Verification:

- Added 3 failing-first provider-response-normalization tests proving unsafe `test_plan` and `rollback_notes` shapes were accepted before implementation.
- `python3 -m pytest tests/test_provider_response_normalization.py::test_provider_candidate_normalization_rejects_test_plan_list_subclass_without_leak tests/test_provider_response_normalization.py::test_provider_candidate_normalization_rejects_rollback_note_subclass_without_leak tests/test_provider_response_normalization.py::test_provider_candidate_normalization_requires_root_text_lists -q`: failed before implementation because unsafe root text-list shapes were accepted.
- `python3 -m pytest tests/test_provider_response_normalization.py tests/test_anthropic_provider.py tests/test_openai_provider.py -q`: 138 tests passed.
- `ruff check src/jedi_devproject/provider_response_normalization.py tests/test_provider_response_normalization.py tests/test_anthropic_provider.py tests/test_openai_provider.py`: all checks passed.
- `ruff check src tests`: all checks passed.
- `mypy src tests`: success with no issues in 197 source files.
- `python3 -m pytest tests/test_project_docs.py -q`: 730 tests passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2814 tests passed with 93.01% total coverage.
