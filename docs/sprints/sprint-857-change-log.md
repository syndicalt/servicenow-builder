# Sprint 857 Change Log - Failure notifier state-choice guard

## Intent

Harden failure-notifier Draft-state discovery so malformed state-choice records
from an alternate ServiceNow client cannot replace failed-story writeback with a
secondary state-choice exception.

## Changes

- Added 1 failing-first failure notifier state-choice assertion: `tests/test_runtime.py::test_servicenow_failure_notifier_skips_malformed_state_choices`.
- Added 1 failing-first sprint documentation assertion: `tests/test_project_docs.py::test_sprint_857_documents_failure_notifier_state_choice_guard`.
- `test_servicenow_failure_notifier_skips_malformed_state_choices` verifies hostile state-choice labels are skipped before matching the valid Draft choice.
- `_story_state_choice_value()` now ignores malformed state-choice records before label comparison or state value return.

## Verification

- `pytest tests/test_runtime.py::test_servicenow_failure_notifier_skips_malformed_state_choices tests/test_project_docs.py::test_sprint_857_documents_failure_notifier_state_choice_guard -q` - 2 passed.
- `pytest tests/test_runtime.py -q -k "servicenow_failure_notifier"` - 7 passed, 410 deselected.
- `pytest tests/test_project_docs.py -q` - 930 passed.
- `pytest --cov=src/jedi_devproject --cov-report=term-missing -q` - 3411 passed, 93.48% coverage.
