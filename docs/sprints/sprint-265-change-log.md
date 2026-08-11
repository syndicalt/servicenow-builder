# Sprint 265 Change Log - Reviewed Update Set XML Bounded Validation

## Summary

- Reviewed delivery artifact job creation now validates Update Set XML with bounded binary scans instead of `Path.read_text()`.
- Added a failing regression proving reviewed Update Set XML validation does not perform a whole-file text read.
- Preserved the reviewed export contract: smoke placeholder XML is rejected, empty unload XML fails closed, and real Update Set XML must contain a `sys_update_xml` customer update marker.
- The validator keeps only small marker windows in memory and fails closed with `reviewed_export_artifact_required` when the required marker is not found inside the bounded scan window.
- Documented bounded reviewed Update Set XML validation in the operator guide.

## Verification

- `python3 -m pytest tests/test_artifact_handoff.py::test_reviewed_delivery_artifact_job_validates_xml_without_whole_file_text_read tests/test_artifact_handoff.py::test_reviewed_delivery_artifact_job_records_contract_and_hash tests/test_artifact_handoff.py::test_reviewed_delivery_artifact_job_rejects_smoke_placeholder_xml tests/test_artifact_handoff.py::test_reviewed_delivery_artifact_job_rejects_empty_update_set_xml tests/test_artifact_handoff.py::test_handoff_report_hashes_artifacts_without_whole_file_read -q` - 5 passed.
- `python3 -m pytest tests/test_artifact_handoff.py::test_reviewed_delivery_artifact_job_validates_xml_without_whole_file_text_read tests/test_artifact_handoff.py::test_reviewed_delivery_artifact_job_records_contract_and_hash tests/test_artifact_handoff.py::test_reviewed_delivery_artifact_job_rejects_smoke_placeholder_xml tests/test_artifact_handoff.py::test_reviewed_delivery_artifact_job_rejects_empty_update_set_xml tests/test_project_docs.py::test_sprint_two_hundred_sixty_five_documents_xml_validation -q` - 5 passed.
- `python3 -m ruff check src/jedi_devproject/artifact_handoff.py tests/test_artifact_handoff.py tests/test_project_docs.py` - all checks passed.
- `python3 -m mypy src/jedi_devproject/artifact_handoff.py tests/test_artifact_handoff.py tests/test_project_docs.py` - success: no issues found in 3 source files.
- `python3 -m ruff check src tests` - all checks passed.
- `python3 -m mypy src tests` - success: no issues found in 174 source files.
- `python3 -m pytest tests/test_project_docs.py -q` - 339 passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 1662 passed, total coverage 93.97%.
