# Sprint 326 Change Log

Scope: Production hardening - Intent and Artifact Generation Validation Input Redaction.

## Summary

- Normalized automation intent validation now suppresses rejected input values in Pydantic validation errors.
- Artifact generation validation now suppresses rejected input values across Business Rule, Client Script, Script Include, UI Policy, catalog item, catalog UI policy, catalog client script, record producer, Flow Designer evidence, and ATF test plan schemas.
- Existing `extra="forbid"` fail-closed validation remains in place. The change only prevents invalid story/model payload fragments from being reflected in diagnostics.
- Direct validation diagnostics still name invalid fields and stable validation reasons, but do not echo rejected story contract fragments, generated script bodies, catalog variable names, UI conditions, Flow graph evidence, or ATF candidate details into logs, artifacts, or ServiceNow work notes.

## Verification

- `python3 -m pytest tests/test_automation_intent.py::test_automation_intent_validation_errors_do_not_echo_rejected_inputs -q` - 1 test failed before implementation because direct automation intent validation echoed `input_value='secret-source'`.
- `python3 -m pytest tests/test_generation_validators.py::test_artifact_generation_validation_errors_do_not_echo_rejected_inputs -q` - 1 test failed before implementation because direct artifact generation validation echoed `input_value='secret-when'`.
- `python3 -m pytest tests/test_automation_intent.py::test_automation_intent_validation_errors_do_not_echo_rejected_inputs tests/test_generation_validators.py::test_artifact_generation_validation_errors_do_not_echo_rejected_inputs -q` - 2 passed after implementation.
- `python3 -m pytest tests/test_automation_intent.py tests/test_generation_validators.py tests/test_catalog_item_generation.py tests/test_catalog_ui_policy_generation.py tests/test_catalog_client_script_generation.py tests/test_record_producer_generation.py tests/test_atf_test_generation.py tests/test_project_docs.py::test_sprint_three_hundred_twenty_six_documents_intent_generation_error_redaction -q` - 237 passed.
- `python3 -m ruff check src tests` - all checks passed.
- `python3 -m mypy src tests` - no issues found in 181 source files.
- `python3 -m pytest tests/test_project_docs.py -q` - 400 passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 1954 passed, total coverage 93.92%.
