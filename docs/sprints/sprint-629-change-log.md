# Sprint 629 Change Log

## Admin alert row exact-string rendering

Sprint 629 continued production hardening by tightening `_admin_alert_row()`, the HTML admin console boundary that renders operational alert severity and detail values. The JSON alert projection normally returns sanitized strings, but the HTML renderer still coerced projected values with `str()`. If a malformed in-process alert projection supplied hostile objects, rendering `/admin` could raise a secondary exception or leak diagnostic fragments.

Admin alert rows now render `severity` and `detail` only when the projected values are exact strings. Malformed, string-subclass, non-string, or unstringifiable projected values collapse to fixed fallback text before HTML escaping. Valid alert output remains unchanged.

Verification:

- Added 1 failing-first runtime test proving hostile admin alert response text executed before implementation.
- `python3 -m pytest tests/test_runtime.py::test_admin_alert_row_rejects_malformed_response_text_without_leak -q`: failed before implementation with the hostile `admin-alert-secret` exception.
- `python3 -m pytest tests/test_runtime.py::test_admin_alert_row_rejects_malformed_response_text_without_leak tests/test_runtime.py::test_admin_console_renders_operational_alerts tests/test_runtime.py::test_admin_console_renders_stale_running_alerts -q`: 3 tests passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 703 documentation tests passed.
- `python3 -m ruff check src tests`: passed.
- `python3 -m mypy src tests`: passed with no issues in 197 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2746 tests passed at 93.07% coverage.
