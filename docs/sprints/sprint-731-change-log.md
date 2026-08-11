# Sprint 731 Change Log - ServiceNow attachment read cause boundary

## Scope

Hardened ServiceNow attachment upload read diagnostics so local artifact read failures do not retain
unsafe `ArtifactReadError` instances as public `ServiceNowApiError` causes.

## Tests First

- Added 3 failing-first ServiceNow attachment read cause assertions:
  - `tests/test_servicenow.py::test_servicenow_client_rejects_oversized_story_attachment_before_reading`
  - `tests/test_servicenow.py::test_servicenow_client_rejects_symlinked_story_attachment_before_upload`
  - `tests/test_servicenow.py::test_servicenow_client_attachment_read_error_uses_typed_reason_not_message_prefix`
- Initial failures proved the public `ServiceNowApiError` retained `ArtifactReadError` causes for:
  - `oversized.xml` oversized attachment rejection.
  - `attachment-client_secret=path-secret.xml` symlinked attachment rejection.
  - `spoofed-message` typed-reason spoofing protection.
- Added 1 failing-first documentation assertion:
  `tests/test_project_docs.py::test_sprint_731_documents_servicenow_attachment_read_cause_boundary`
- Initial documentation failure proved this sprint log did not exist yet.

## Changes

- Suppressed original `ArtifactReadError` causes when oversized attachment artifacts are rejected.
- Suppressed original `ArtifactReadError` causes when symlinked, missing, spoofed, or non-regular
  attachment artifacts are rejected.
- Preserved typed `ArtifactReadError.reason` classification so spoofed message prefixes cannot
  influence whether an error is treated as oversized or non-regular.
- Preserved the existing fixed diagnostics:
  - `ServiceNow attachment file exceeds 10485760 bytes`
  - `ServiceNow attachment file must be a regular file`
- Documented the ServiceNow attachment read cause boundary in the operator guide.

## Verification

- `python3 -m pytest tests/test_servicenow.py -q -k "oversized_story_attachment or symlinked_story_attachment or attachment_read_error_uses_typed_reason"`
  failed first with 3 failures.
- `python3 -m pytest tests/test_project_docs.py -q -k sprint_731` failed first with 1 failure.
- `python3 -m pytest tests/test_servicenow.py -q -k "oversized_story_attachment or symlinked_story_attachment or attachment_read_error_uses_typed_reason or uploads_story_attachment_without_whole_file_read"`
  passed with 4 tests and 284 deselected.
- `python3 -m pytest tests/test_project_docs.py -q -k sprint_731` passed with 1 test and 804
  deselected.
- `ruff check src tests` passed.
- `mypy src tests` passed with no issues in 197 source files.
- `python3 -m pytest tests/test_servicenow.py -q` passed with 288 tests.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` passed with
  3058 tests and 93.33% total coverage.
