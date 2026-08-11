# Sprint 849 Change Log - Work-note literal secret-values guard

## Intent

Harden ServiceNow work-note literal secret redaction so direct callers cannot
crash work-note formatting by passing hostile iterators, non-string secret
entries, or string subclasses through `secret_values`.

## Changes

- Added 2 failing-first work-note secret-values assertions: `tests/test_work_note_safety.py::test_safe_work_note_value_ignores_hostile_secret_iterator_for_exact_strings` and `tests/test_work_note_safety.py::test_safe_work_note_value_ignores_non_exact_literal_secret_values`.
- Added 1 failing-first sprint documentation assertion: `tests/test_project_docs.py::test_sprint_849_documents_work_note_secret_values_guard`.
- Literal `secret_values` are projected to a bounded exact-string set before replacement.
- Hostile iterators such as `_HostileSecretValues` fail closed without surfacing iterator exception text.
- Non-string and string-subclass entries such as `_SecretValueSubclass` are ignored before literal redaction.

## Verification

- `pytest tests/test_work_note_safety.py::test_safe_work_note_value_rejects_string_subclasses_without_coercion tests/test_work_note_safety.py::test_safe_work_note_value_ignores_hostile_secret_iterator_for_exact_strings tests/test_work_note_safety.py::test_safe_work_note_value_ignores_non_exact_literal_secret_values tests/test_project_docs.py::test_sprint_849_documents_work_note_secret_values_guard -q` - 4 passed.
- `pytest tests/test_work_note_safety.py tests/test_runtime.py tests/test_update_set_handoff.py tests/test_artifact_handoff.py tests/test_cli_io.py tests/test_capability_assessment.py tests/test_model_fulfillment.py -q` - 530 passed.
- `pytest tests/test_project_docs.py -q` - 922 passed.
- `pytest --cov=src/jedi_devproject --cov-report=term-missing -q` - 3390 passed, 93.44% coverage.
