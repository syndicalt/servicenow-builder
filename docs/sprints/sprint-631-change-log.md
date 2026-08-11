# Sprint 631 Change Log

## Delivery attachment audit exact-string response metadata

Sprint 631 continued production hardening by tightening the local attachment audit written after `attach-delivery-artifacts --apply`. The command previously converted both validated delivery-job fields and the ServiceNow Attachment API response `sys_id` with `str()` while building the audit payload. If the attachment response contained hostile in-process metadata, audit creation could raise a secondary exception or leak response fragments after the file had already been uploaded.

Attachment audit construction now reads delivery-job artifact fields only when they are exact strings. Malformed delivery-job values fail with `artifact_handoff_report_invalid`. The external attachment response `sys_id` is accepted only when it is a non-empty exact string; missing, empty, non-string, string-subclass, or unstringifiable response values are recorded as `[attachment sys_id unavailable]` so post-upload audit evidence is still written without invoking custom conversion.

Verification:

- Added 1 failing-first CLI test proving hostile attachment response `sys_id` values executed before implementation.
- `python3 -m pytest tests/test_cli.py::test_cli_attach_delivery_artifacts_audit_rejects_malformed_attachment_sys_id -q`: failed before implementation with the hostile `attachment-sys-id-secret` exception.
- `python3 -m pytest tests/test_cli.py::test_cli_attach_delivery_artifacts_audit_rejects_malformed_attachment_sys_id tests/test_cli.py::test_cli_attach_delivery_artifacts_requires_confirmation_to_apply tests/test_cli.py::test_cli_write_artifact_handoff_summary_rejects_non_string_story_number tests/test_cli.py::test_cli_attach_delivery_artifacts_rejects_non_string_story_number -q`: 4 tests passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 705 documentation tests passed.
- `python3 -m ruff check src tests`: passed.
- `python3 -m mypy src tests`: passed with no issues in 197 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2751 tests passed at 93.07% coverage.
