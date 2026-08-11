# Sprint 607 Change Log

## Alert sink response truncation marker collision safety

Sprint 607 continued production hardening by preserving user-provided alert sink response fields when the bounded response diagnostic adds its internal truncation marker. Alert response diagnostics already sampled wide dictionaries and added `__jedi_response_truncated__`, but that marker was inserted with a fixed key. If the sink response already contained the same key, the internal marker overwrote the original response value and silently lost evidence in `AlertDeliveryError`.

`_redact_alert_response_node()` now inserts the internal `__jedi_response_truncated__` field through `_unique_alert_response_key()`. User-provided marker fields remain visible, and the internal truncation marker receives a deterministic duplicate suffix such as `__jedi_response_truncated__ [duplicate 2]`.

Verification:

- Added 1 failing-first alert response diagnostic test proving the internal truncation marker overwrote a user-provided `__jedi_response_truncated__` field before implementation.
- `python3 -m pytest tests/test_alert_delivery.py::test_alert_response_diagnostic_preserves_user_truncation_marker_key -q`: failed before implementation because the original user marker value was replaced by the internal truncation metadata.
- `python3 -m pytest tests/test_alert_delivery.py::test_alert_response_diagnostic_preserves_user_truncation_marker_key tests/test_alert_delivery.py::test_alert_response_diagnostic_does_not_consume_all_fields_for_wide_response tests/test_alert_delivery.py::test_emit_alert_webhook_failure_bounds_whole_structured_response_diagnostic -q`: 3 passed.
- `python3 -m pytest tests/test_project_docs.py::test_sprint_607_documents_alert_sink_response_truncation_marker_collision tests/test_project_docs.py::test_sprint_604_documents_alert_delivery_text_normalization -q`: 2 passed.
- `python3 -m pytest tests/test_alert_delivery.py -q`: 68 passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 681 passed.
- `python3 -m ruff check src tests`: all checks passed.
- `python3 -m mypy src tests`: success, no issues found in 196 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2692 passed, total coverage 93.15%, required 90% coverage reached.
