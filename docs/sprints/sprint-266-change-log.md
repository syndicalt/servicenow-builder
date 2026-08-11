# Sprint 266 Change Log - Shared Streaming Artifact Hashes

## Summary

- Added a shared artifact SHA-256 helper that streams files in bounded chunks.
- Replaced remaining production artifact hash call sites that used `Path.read_bytes()` in lifecycle manifests, intake feedback artifact refs, delivery attachment hash verification, and reviewed handoff paths.
- Added failing regressions for lifecycle manifest hashing, intake feedback artifact hashing, and delivery attachment dry-run hash verification to prove those paths reject whole-file reads.
- Preserved existing hash mismatch behavior, write-once audit behavior, reviewed handoff behavior, and 64-character SHA-256 output.
- Documented shared streaming artifact hashes in the operator guide.

## Verification

- `python3 -m pytest tests/test_writeback_audit.py::test_lifecycle_manifest_hashes_artifacts_without_whole_file_read tests/test_fulfillment_handler.py::test_intake_feedback_artifact_hash_uses_streaming_read tests/test_cli.py::test_cli_attach_delivery_artifacts_hash_check_uses_streaming_read tests/test_artifact_handoff.py::test_handoff_report_hashes_artifacts_without_whole_file_read tests/test_artifact_handoff.py::test_reviewed_delivery_artifact_job_validates_xml_without_whole_file_text_read -q` - 5 passed.
- `python3 -m pytest tests/test_writeback_audit.py::test_lifecycle_manifest_hashes_artifacts_without_whole_file_read tests/test_fulfillment_handler.py::test_intake_feedback_artifact_hash_uses_streaming_read tests/test_cli.py::test_cli_attach_delivery_artifacts_hash_check_uses_streaming_read tests/test_artifact_handoff.py::test_handoff_report_hashes_artifacts_without_whole_file_read tests/test_project_docs.py::test_sprint_two_hundred_sixty_six_documents_shared_streaming_hashes -q` - 5 passed.
- `python3 -m ruff check src/jedi_devproject/artifacts.py src/jedi_devproject/artifact_handoff.py src/jedi_devproject/fulfillment_handler.py src/jedi_devproject/cli_delivery.py tests/test_writeback_audit.py tests/test_fulfillment_handler.py tests/test_cli.py tests/test_project_docs.py` - all checks passed.
- `python3 -m mypy src/jedi_devproject/artifacts.py src/jedi_devproject/artifact_handoff.py src/jedi_devproject/fulfillment_handler.py src/jedi_devproject/cli_delivery.py tests/test_writeback_audit.py tests/test_fulfillment_handler.py tests/test_cli.py tests/test_project_docs.py` - success: no issues found in 8 source files.
- `python3 -m ruff check src tests` - all checks passed.
- `python3 -m mypy src tests` - success: no issues found in 174 source files.
- `python3 -m pytest tests/test_project_docs.py -q` - 340 passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 1666 passed, total coverage 93.97%.
