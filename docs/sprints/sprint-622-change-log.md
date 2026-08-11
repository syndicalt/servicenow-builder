# Sprint 622 Change Log

## Artifact handoff delivery job fail-closed validation

Sprint 622 continued production hardening by tightening `delivery_attachment_jobs_from_report()`, the handoff report boundary that turns reviewed delivery decisions into ServiceNow attachment jobs. The previous path coerced `story_number` and attachment fields with `str()` and relied on truthiness for `attach_to_servicenow`, which meant malformed in-process report dictionaries could execute hostile `__str__` or `__bool__` hooks before producing delivery jobs.

Delivery job extraction now validates the report shape before generating attachment jobs. It requires an exact string story number, a list of dictionary decisions, an exact boolean `attach_to_servicenow` flag, and exact non-empty string attachment fields. Malformed report shapes or unsupported Python values fail with the fixed `artifact_handoff_report_invalid` diagnostic without echoing report values. Existing business-rule diagnostics for reviewed export contract and artifact hash failures remain unchanged.

Verification:

- Added 2 failing-first artifact handoff tests proving hostile delivery text and hostile attach flags executed before implementation.
- `python3 -m pytest tests/test_artifact_handoff.py::test_delivery_attachment_jobs_reject_hostile_text_without_coercion tests/test_artifact_handoff.py::test_delivery_attachment_jobs_reject_hostile_attach_flag_without_truthiness -q`: failed before implementation with hostile assertion errors.
- `python3 -m pytest tests/test_artifact_handoff.py -q`: 21 tests passed.
- `python3 -m pytest tests/test_artifact_handoff.py tests/test_project_docs.py::test_sprint_622_documents_artifact_handoff_delivery_job_validation -q`: 22 tests passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 696 documentation tests passed.
- `python3 -m ruff check src tests`: passed.
- `python3 -m mypy src tests`: passed with no issues in 197 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2729 tests passed at 93.06% coverage.
