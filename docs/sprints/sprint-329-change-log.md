# Sprint 329 Change Log

Scope: Production hardening - discovery and Flow evidence validation input redaction.

## Summary

- Discovery and Flow evidence DTO validation now suppresses rejected input values in Pydantic validation errors.
- The covered boundary includes discovered table fields, form elements, form sections, instance discovery contexts, ServiceNow surface records, surface context bundles, Flow retrieved node evidence, generated Flow customer updates, Flow build results, Flow graph states, Flow round-trip reports, Flow XML shape evidence records, snapshot evidence records, and Flow XML evidence bundles.
- Existing fail-closed validation remains in place. Diagnostics still name invalid fields and stable reasons, but type, enum, parser, extra-field, and bounds failures do not echo rejected instance metadata, script summaries, surface records, graph node details, XML evidence identifiers, payload snippets, graph hashes, snapshot ids, or round-trip assertion details into logs, artifacts, or ServiceNow work notes.

## Verification

- `python3 -m pytest tests/test_context_flow_dto_redaction.py::test_context_and_flow_dto_validation_errors_do_not_echo_rejected_inputs -q` - 1 test failed before implementation because direct discovery context validation echoed `input_value='secret-max-length'`.
- `python3 -m pytest tests/test_context_flow_dto_redaction.py::test_context_and_flow_dto_validation_errors_do_not_echo_rejected_inputs tests/test_instance_discovery.py tests/test_flow_builder.py tests/test_flow_roundtrip.py tests/test_flow_xml_evidence.py -q` - 89 passed after implementation.
- `python3 -m pytest tests/test_context_flow_dto_redaction.py::test_context_and_flow_dto_validation_errors_do_not_echo_rejected_inputs tests/test_project_docs.py::test_sprint_three_hundred_twenty_nine_documents_discovery_flow_error_redaction -q` - 2 passed.
- `python3 -m ruff check src tests` - all checks passed.
- `python3 -m mypy src tests` - no issues found in 183 source files.
- `python3 -m pytest tests/test_project_docs.py -q` - 403 passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 1960 passed, total coverage 93.92%.
