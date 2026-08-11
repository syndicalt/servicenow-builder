# Sprint 345 Change Log

Scope: Production hardening - ServiceNow transport redirect blocking.

## Summary

- ServiceNow OAuth, Table API, and Attachment API calls now build an explicit urllib opener with a no-redirect handler instead of using default `urlopen()` behavior.
- Any 3xx redirect is blocked before a second outbound request can be made, so configured ServiceNow instance boundaries remain authoritative for credentials, bearer tokens, story content, and delivery artifacts.
- Existing request encoding, JSON parsing, HTTP-error shaping, successful-response byte caps, and HTTP-error byte caps are preserved.
- The ServiceNow transport tests now patch the opener factory directly so redirect-handler installation is covered by the same boundary used in production.

## Verification

- `python3 -m pytest tests/test_servicenow.py::test_urllib_transport_installs_no_redirect_handler tests/test_servicenow.py::test_urllib_transport_blocks_redirect_before_following tests/test_servicenow.py::test_urllib_transport_encodes_query_and_form_body -q` - 3 tests failed before implementation because the transport still used default `urlopen()` behavior and exposed no redirect handler.
- `python3 -m pytest tests/test_servicenow.py::test_urllib_transport_installs_no_redirect_handler tests/test_servicenow.py::test_urllib_transport_blocks_redirect_before_following tests/test_servicenow.py::test_urllib_transport_encodes_query_and_form_body tests/test_servicenow.py::test_urllib_transport_returns_json_body_for_http_error_response -q` - 4 passed after implementation.
- `python3 -m pytest tests/test_servicenow.py -q` - 78 passed.
- `python3 -m pytest tests/test_project_docs.py::test_sprint_three_hundred_forty_five_documents_servicenow_redirect_blocking tests/test_servicenow.py -q` - 79 passed.
- `python3 -m ruff check src tests` - all checks passed.
- `python3 -m mypy src tests` - no issues found in 187 source files.
- `python3 -m pytest tests/test_project_docs.py -q` - 419 passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 2002 passed, total coverage 94.05%.
