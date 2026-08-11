# Sprint 858 Change Log - Failure notifier state-choice value guard

## Intent

Harden failure-notifier Draft-state discovery so exact-string but unsafe
state-choice values cannot be written back as the failed story state when an
alternate ServiceNow client returns malformed metadata.

## Changes

- Added 1 failing-first failure notifier state-choice value assertion: `tests/test_runtime.py::test_servicenow_failure_notifier_skips_unsafe_state_choice_values`.
- Added 1 failing-first sprint documentation assertion: `tests/test_project_docs.py::test_sprint_858_documents_failure_notifier_state_choice_value_guard`.
- `test_servicenow_failure_notifier_skips_unsafe_state_choice_values` verifies control-character-bearing state values are skipped before the valid Draft state is selected.
- `_story_state_choice_value()` now rejects unsafe exact-string state-choice labels and values before returning the state.

## Verification

- `pytest tests/test_runtime.py::test_servicenow_failure_notifier_skips_unsafe_state_choice_values tests/test_project_docs.py::test_sprint_858_documents_failure_notifier_state_choice_value_guard -q` - 2 passed.
- `pytest tests/test_runtime.py -q -k "servicenow_failure_notifier"` - 8 passed, 410 deselected.
- `pytest tests/test_project_docs.py -q` - 931 passed.
- `pytest --cov=src/jedi_devproject --cov-report=term-missing -q` - 3413 passed, 93.48% coverage.
