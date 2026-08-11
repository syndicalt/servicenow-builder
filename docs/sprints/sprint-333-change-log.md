# Sprint 333 Change Log

Scope: Production hardening - bootstrap, enrichment, and risk DTO validation input redaction.

## Summary

- Bootstrap, enrichment, and risk DTO validation now suppresses rejected input values in Pydantic validation errors.
- The covered boundary includes bootstrap field specs, bootstrap field plans, bootstrap apply results, lifecycle webhook bootstrap specs, lifecycle webhook apply and verification results, Update Set importer bootstrap specs, Update Set importer apply results, story enrichment results, and risk inputs.
- Existing validation remains in place. Diagnostics still name invalid fields and stable reasons, but type, parser, and nested-model failures do not echo rejected bootstrap field values, lifecycle endpoint details, generated business-rule scripts, retrieved update-set importer scripts, story enrichment payloads, or risk flags into logs, artifacts, or ServiceNow work notes.
- A project-wide Pydantic DTO audit now reports zero `BaseModel` classes without `hide_input_in_errors`.

## Verification

- `python3 -m pytest tests/test_bootstrap_legacy_dto_redaction.py::test_bootstrap_legacy_dto_validation_errors_do_not_echo_rejected_inputs -q` - 1 test failed before implementation because direct bootstrap field spec validation echoed `input_value='sprint-333-secret-BootstrapFieldSpec'`.
- `python3 -m pytest tests/test_bootstrap_legacy_dto_redaction.py::test_bootstrap_legacy_dto_validation_errors_do_not_echo_rejected_inputs tests/test_bootstrap.py tests/test_enrichment.py tests/test_risk.py -q` - 31 passed after implementation.
- Project-wide Pydantic DTO audit - `missing 0`.
- `python3 -m pytest tests/test_bootstrap_legacy_dto_redaction.py::test_bootstrap_legacy_dto_validation_errors_do_not_echo_rejected_inputs tests/test_project_docs.py::test_sprint_three_hundred_thirty_three_documents_bootstrap_legacy_error_redaction -q` - 2 passed.
- `python3 -m ruff check src tests` - all checks passed.
- `python3 -m mypy src tests` - no issues found in 187 source files.
- `python3 -m pytest tests/test_project_docs.py -q` - 407 passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 1968 passed, total coverage 93.95%.
