# Sprint 331 Change Log

Scope: Production hardening - capability, planning, safety, and review DTO validation input redaction.

## Summary

- Capability, planning, safety, and review DTO validation now suppresses rejected input values in Pydantic validation errors.
- The covered boundary includes field/form intents, capability profiles, story capability assessments, intake feedback, surface operations, surface operation plans, allowlist policies, eligibility results, review settings, review events, review results, repointing suggestions, and run metrics.
- Existing validation remains in place. Diagnostics still name invalid fields and stable reasons, but type, enum, parser, extra-field, and bounds failures do not echo rejected field labels, placement directives, capability names, unsupported cases, operator feedback, suggested stories, surface targets, allowlist values, eligibility reasons, reviewer ids, review reasons, prioritization evidence, or run metrics into logs, artifacts, or ServiceNow work notes.

## Verification

- `python3 -m pytest tests/test_capability_planning_dto_redaction.py::test_capability_planning_dto_validation_errors_do_not_echo_rejected_inputs -q` - 1 test failed before implementation because direct capability intent validation echoed `input_value='secret-position'`.
- `python3 -m pytest tests/test_capability_planning_dto_redaction.py::test_capability_planning_dto_validation_errors_do_not_echo_rejected_inputs tests/test_capabilities.py tests/test_capability_assessment.py tests/test_surface_planning.py tests/test_safety.py tests/test_review.py tests/test_planning.py -q` - 49 passed after implementation.
- `python3 -m pytest tests/test_capability_planning_dto_redaction.py::test_capability_planning_dto_validation_errors_do_not_echo_rejected_inputs tests/test_project_docs.py::test_sprint_three_hundred_thirty_one_documents_capability_planning_error_redaction -q` - 2 passed.
- `python3 -m ruff check src tests` - all checks passed.
- `python3 -m mypy src tests` - no issues found in 185 source files.
- `python3 -m pytest tests/test_project_docs.py -q` - 405 passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 1964 passed, total coverage 93.94%.
