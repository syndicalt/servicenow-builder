# Sprint 335 Change Log

Scope: Production hardening - CLI validation diagnostic redaction.

## Summary

- Bootstrap and delivery CLI commands now redact caught exception diagnostics before printing validation failure details to stdout.
- The shared CLI renderer preserves stable reason codes such as `invalid_build_result`, `invalid_lifecycle_webhook_spec`, and `json_input_too_large`, but redacts URL credentials, sensitive query parameters, Authorization header values, cookie values, private-key blocks, and sensitive assignment fragments such as `client_secret=...`.
- This hardens operator terminals, CI logs, and copied support output when local input paths or malformed values contain secret material.

## Verification

- `python3 -m pytest tests/test_cli.py::test_cli_process_external_build_result_redacts_invalid_input_path_details tests/test_cli.py::test_cli_apply_lifecycle_webhook_redacts_invalid_spec_path_details -q` - 2 tests failed before implementation because CLI output printed raw `external-build-secret` and `lifecycle-spec-secret` path fragments.
- `python3 -m pytest tests/test_cli.py::test_cli_process_external_build_result_redacts_invalid_input_path_details tests/test_cli.py::test_cli_apply_lifecycle_webhook_redacts_invalid_spec_path_details tests/test_cli_io.py tests/test_cli.py::test_cli_process_external_build_result_writes_writeback_and_delivery_jobs tests/test_cli.py::test_cli_apply_lifecycle_webhook_requires_confirmation_without_mutation tests/test_cli.py::test_cli_apply_update_set_importer_requires_confirmation_without_mutation -q` - 7 passed after implementation.
- `python3 -m pytest tests/test_cli.py tests/test_cli_io.py -q` - 66 passed.
- `python3 -m pytest tests/test_cli.py::test_cli_process_external_build_result_redacts_invalid_input_path_details tests/test_cli.py::test_cli_apply_lifecycle_webhook_redacts_invalid_spec_path_details tests/test_project_docs.py::test_sprint_three_hundred_thirty_five_documents_cli_validation_diagnostic_redaction -q` - 3 passed.
- `python3 -m ruff check src tests` - all checks passed.
- `python3 -m mypy src tests` - no issues found in 187 source files.
- `python3 -m pytest tests/test_project_docs.py -q` - 409 passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 1973 passed, total coverage 93.99%.
