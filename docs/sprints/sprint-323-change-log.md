# Sprint 323 Change Log - ServiceNow Boundary Validation Input Redaction

## Summary

- Direct ServiceNow boundary model validation now suppresses rejected input values in Pydantic validation errors.
- `ServiceNowSettings`, `HttpRequest`, `HttpResponse`, `StoryStateChoice`, and `StoryDictionaryField` still name invalid fields without echoing raw rejected values.
- The redaction boundary covers direct ServiceNow instance URLs, request URLs, nested request header values, request body fragments, response status parsing text, and live instance metadata before diagnostics can reach logs, artifacts, or ServiceNow work notes.
- Existing ServiceNow request sanitization, HTTP response bounds, OAuth flow behavior, and client tests remain intact.
- Documented the ServiceNow boundary model diagnostic behavior in the operator guide.

## Verification

- `python3 -m pytest tests/test_servicenow.py::test_servicenow_boundary_validation_errors_do_not_echo_rejected_inputs -q` - 4 tests failed before implementation because direct ServiceNow model validation errors included `input_value`.
- `python3 -m pytest tests/test_servicenow.py::test_servicenow_boundary_validation_errors_do_not_echo_rejected_inputs tests/test_servicenow.py -q` - 73 passed after implementation.
- `python3 -m pytest tests/test_servicenow.py::test_servicenow_boundary_validation_errors_do_not_echo_rejected_inputs tests/test_project_docs.py::test_sprint_three_hundred_twenty_three_documents_servicenow_boundary_error_redaction -q` - 5 passed.
- `python3 -m ruff check src/jedi_devproject/servicenow.py tests/test_servicenow.py tests/test_project_docs.py` - all checks passed.
- `python3 -m mypy src/jedi_devproject/servicenow.py tests/test_servicenow.py tests/test_project_docs.py` - no issues found in 3 source files.
- `python3 -m ruff check src tests` - all checks passed.
- `python3 -m mypy src tests` - no issues found in 181 source files.
- `python3 -m pytest tests/test_project_docs.py -q` - 397 passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 1938 passed, total coverage 93.87%.
