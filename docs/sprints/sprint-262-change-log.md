# Sprint 262 Change Log - Admin Diagnostic Streaming Body Bound

## Summary

- Admin diagnostic request-size enforcement now validates the actual streamed request body instead of relying only on `Content-Length`.
- Added a failing regression proving an oversized admin diagnostic stream without `Content-Length` returns `413`.
- Updated the admin middleware to reject malformed or oversized declared lengths early, otherwise read and replay a bounded body for downstream handlers.
- Preserved the existing behavior that oversized admin diagnostic requests are rejected before auth, artifact, job, or list handlers touch the operational store.
- Documented that missing or misleading length headers do not bypass the admin diagnostic body cap.

## Verification

- `python3 -m pytest tests/test_runtime.py::test_admin_json_endpoint_rejects_oversized_request_body_before_store_access tests/test_runtime.py::test_admin_request_size_error_rejects_oversized_stream_without_content_length tests/test_runtime.py::test_admin_artifact_endpoint_rejects_oversized_request_body_before_store_access tests/test_runtime.py::test_artifact_read_requires_admin_bearer_token -q` - 4 passed.
- `python3 -m ruff check src/jedi_devproject/admin_routes.py tests/test_runtime.py` - all checks passed.
- `python3 -m mypy src/jedi_devproject/admin_routes.py tests/test_runtime.py` - success: no issues found in 2 source files.
- `python3 -m pytest tests/test_runtime.py::test_admin_json_endpoint_rejects_oversized_request_body_before_store_access tests/test_runtime.py::test_admin_request_size_error_rejects_oversized_stream_without_content_length tests/test_runtime.py::test_admin_artifact_endpoint_rejects_oversized_request_body_before_store_access tests/test_runtime.py::test_artifact_read_requires_admin_bearer_token tests/test_project_docs.py::test_sprint_two_hundred_sixty_two_documents_admin_streaming_body_bound -q` - 5 passed.
- `python3 -m ruff check src/jedi_devproject/admin_routes.py tests/test_runtime.py tests/test_project_docs.py` - all checks passed.
- `python3 -m ruff check src tests` - all checks passed.
- `python3 -m mypy src tests` - success: no issues found in 174 source files.
- `python3 -m pytest tests/test_project_docs.py -q` - 336 passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 1656 passed, total coverage 93.96%.
