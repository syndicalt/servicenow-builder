# Sprint 650 Change Log

## Generic provider response exact identifier boundary

Sprint 650 continued production hardening by tightening the generic provider-policy validator used by `generate_with_provider()`. That validator checked table, operation, and sys_id allowlists, but it coerced model response values with `str()` before comparison. A malformed in-process provider response could use hostile table, operation, or sys_id objects that executed string conversion before validation failed.

Provider response change identifiers now must be exact strings before allowlist checks or diagnostic rendering. Change `table`, `operation`, and non-null `sys_id` values fail closed with `table must be an exact string`, `operation must be an exact string`, or `sys_id must be an exact string` when they are non-string values or string subclasses. Existing rejected exact-string diagnostics still redact, normalize, and cap values before raising `ModelResponseError`.

Verification:

- Added 1 failing-first provider test proving a hostile operation object executed `__str__` before implementation.
- Added explicit post-fix coverage for hostile table and sys_id objects so all three provider response identifiers are pinned.
- `python3 -m pytest tests/test_providers.py::test_model_response_validation_rejects_operation_object_without_leak -q`: failed before implementation because the hostile `__str__` hook ran.
- `python3 -m pytest tests/test_providers.py::test_model_response_validation_rejects_operation_object_without_leak tests/test_providers.py::test_model_response_validation_rejects_table_object_without_leak tests/test_providers.py::test_model_response_validation_rejects_sys_id_object_without_leak tests/test_providers.py::test_model_response_validation_rejects_unsafe_changes tests/test_providers.py::test_model_response_validation_sanitizes_rejected_change_diagnostics tests/test_providers.py::test_approved_provider_receives_minimized_story_fields -q`: 8 tests passed.
- `python3 -m pytest tests/test_project_docs.py::test_sprint_650_documents_generic_provider_response_identifier_boundary -q`: 1 test passed.
- `ruff check src tests`: all checks passed.
- `mypy src tests`: no issues found in 197 source files.
- `python3 -m pytest tests/test_project_docs.py -q`: 724 tests passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2,792 tests passed with 93.00% coverage.
