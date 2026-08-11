# Sprint 433 Change Log

## ServiceNow attachment artifact read typed errors

Hardened ServiceNow attachment upload error classification so it no longer depends on parsing artifact exception message text. Prior behavior in `ServiceNowClient.attach_story_file()` checked `str(exc).startswith("artifact file exceeds ")` to decide whether an `ArtifactReadError` was an oversized attachment or a regular-file safety failure.

`ArtifactReadError` now carries typed metadata through `ArtifactReadError.reason`, with `too_large`, `not_regular`, and `read_failed` reasons. Oversized reads also carry `max_bytes`. The ServiceNow client now branches on `ArtifactReadError.reason` for attachment upload diagnostics, so a misleading or untrusted exception message cannot be classified as an oversized attachment.

Operator-facing failure messages remain stable: oversized files still report `ServiceNow attachment file exceeds 10485760 bytes`, and symlinked or non-regular paths still report `ServiceNow attachment file must be a regular file`.

## Verification

- Added 2 failing-first tests covering typed oversized artifact read metadata and ServiceNow attachment classification that ignores a spoofed `artifact file exceeds` message prefix.
- `python3 -m pytest tests/test_writeback_audit.py tests/test_servicenow.py -q -k "marks_oversized_read_errors or attachment_read_error_uses_typed_reason"`: failed before implementation because `ArtifactReadError` had no typed `reason` and rejected the `reason` constructor argument.
- `python3 -m pytest tests/test_writeback_audit.py tests/test_servicenow.py -q -k "marks_oversized_read_errors or attachment_read_error_uses_typed_reason"`: 2 tests passed.
- `python3 -m ruff check src tests`: all checks passed.
- `python3 -m mypy src tests`: no issues found in 193 source files.
- `python3 -m pytest tests/test_project_docs.py -q`: 507 documentation tests passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2286 total tests passed at 93.96% coverage.
