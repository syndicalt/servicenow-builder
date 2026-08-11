# Sprint 651 Change Log

## Provider field-name exact-string normalization boundary

Sprint 651 continued production hardening by tightening shared provider candidate normalization. Provider adapters normalize model-facing `name/value` field pairs into the internal `fields` dictionary, but the field-name boundary used `isinstance(name, str)` and truthiness before length and character checks. A malformed in-process provider response could pass a string subclass that executed custom string methods before normalization failed.

Provider field entry names now must be non-empty exact strings before emptiness checks, length checks, character scanning, duplicate detection, or dictionary-key insertion. String subclasses and non-string values fail closed with `<Provider> response field entry must include a non-empty exact name`. Existing duplicate, oversized, whitespace, and control-character diagnostics remain fixed and do not echo model-provided field values.

Verification:

- Added 1 failing-first provider-response-normalization test proving a hostile field-name string subclass executed `__len__` before implementation.
- `python3 -m pytest tests/test_provider_response_normalization.py::test_provider_candidate_normalization_rejects_field_name_subclass_without_leak -q`: failed before implementation because the hostile `__len__` hook ran.
- `python3 -m pytest tests/test_provider_response_normalization.py::test_provider_candidate_normalization_rejects_field_name_subclass_without_leak tests/test_provider_response_normalization.py::test_provider_candidate_normalization_rejects_duplicate_field_names tests/test_provider_response_normalization.py::test_provider_candidate_normalization_rejects_unsafe_field_names tests/test_provider_response_normalization.py::test_provider_candidate_normalization_rejects_oversized_field_name -q`: 6 tests passed.
- `python3 -m pytest tests/test_project_docs.py::test_sprint_443_documents_provider_candidate_field_name_normalization tests/test_project_docs.py::test_sprint_651_documents_provider_field_name_exact_string_boundary -q`: 2 tests passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 725 tests passed.
- `ruff check src tests`: all checks passed.
- `mypy src tests`: success with no issues in 197 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2794 tests passed with 93.00% total coverage.
