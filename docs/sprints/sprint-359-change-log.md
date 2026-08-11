# Sprint 359 Change Log

## Whole artifact diagnostic payload bounds

Hardened artifact diagnostic views so a large structured payload cannot create an oversized admin
API response or HTML artifact page. Sprint 358 capped individual diagnostic strings after redaction,
but a stored artifact with many ordinary fields or list entries could still expand into a very large
redacted JSON response through `/artifacts/{artifact_id}` or `/admin/artifacts/{artifact_id}`.

Artifact diagnostic rendering now builds a bounded projection after recursive redaction. If the
redacted payload JSON stays under the cap, the response preserves the existing `payload` shape. If it
exceeds the cap, the API returns `payload_truncated: true` and replaces `payload` with a compact
diagnostic object containing `original_payload_type`, `diagnostic_preview`, and `truncated: true`.
The HTML artifact detail page uses the same projection and labels the view as `payload_truncated`.
The stored artifact row is not modified, and the artifact SHA-256 remains the durable provenance
handle for the full unredacted payload.

## Tests

- Failing-first coverage: 2 tests failed before implementation, proving oversized persisted artifact payloads were redacted but still returned as oversized JSON and HTML diagnostic views.
- Focused verification: `python3 -m pytest tests/test_runtime.py -q -k "bounds_large_persisted_payload"` passed after implementation.
- Artifact regression verification: `python3 -m pytest tests/test_runtime.py -q -k "artifact_read_returns_metadata_and_payload or artifact_read_redacts_sensitive_payload_values or artifact_read_bounds_persisted_diagnostic_payload_strings or admin_console_artifact_view_renders_payload_with_basic_auth or admin_console_artifact_view_redacts_sensitive_payload_values or bounds_large_persisted_payload"` passed with 7 tests.
- Full verification gate: `python3 -m ruff check src tests && python3 -m mypy src tests && python3 -m pytest tests/test_project_docs.py -q && python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` passed with all checks passed, no issues found in 187 source files, 433 documentation tests passed, and 2046 total tests passed at 94.10% coverage.
