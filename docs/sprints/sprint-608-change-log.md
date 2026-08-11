# Sprint 608 Change Log

## Alert sink response exact-string diagnostic boundary

Sprint 608 continued production hardening by requiring exact string values before alert sink response diagnostic key and text redaction. The alert response projector already handled non-string keys and unsupported scalar values without reflecting object internals, but `str` subclasses still passed through the string branches. A hostile or malformed transport could therefore supply subclassed string keys or values that behaved differently from ordinary immutable strings.

`_alert_response_key()` now treats non-exact strings as `[non-string key]`. `_redact_alert_response_node()` now sends non-exact string scalar values through the unsupported scalar path, rendering them as `[non-json value]`. Exact strings remain redacted, whitespace-normalized, and bounded.

Verification:

- Added 2 failing-first alert response diagnostic tests proving string subclass keys and values were accepted by the string branches before implementation.
- `python3 -m pytest tests/test_alert_delivery.py::test_alert_response_diagnostic_rejects_string_subclass_keys_without_stringifying tests/test_alert_delivery.py::test_alert_response_diagnostic_rejects_string_subclass_values_without_methods -q`: failed before implementation because a string subclass key rendered as `client_secret`, and a string subclass value was processed as normal text instead of `[non-json value]`.
- `python3 -m pytest tests/test_alert_delivery.py::test_alert_response_diagnostic_rejects_string_subclass_keys_without_stringifying tests/test_alert_delivery.py::test_alert_response_diagnostic_rejects_string_subclass_values_without_methods tests/test_alert_delivery.py::test_alert_response_diagnostic_normalizes_string_values tests/test_alert_delivery.py::test_alert_response_diagnostic_handles_non_string_response_keys -q`: 4 passed.
- `python3 -m pytest tests/test_project_docs.py::test_sprint_608_documents_alert_sink_response_exact_string_boundary tests/test_project_docs.py::test_sprint_607_documents_alert_sink_response_truncation_marker_collision -q`: 2 passed.
- `python3 -m pytest tests/test_alert_delivery.py -q`: 70 passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 682 passed.
- `python3 -m ruff check src tests`: all checks passed.
- `python3 -m mypy src tests`: success, no issues found in 196 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2695 passed, total coverage 93.15%, required 90% coverage reached.
