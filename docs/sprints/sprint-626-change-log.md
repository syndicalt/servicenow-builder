# Sprint 626 Change Log

## Manual-review feedback exact-string metadata boundary

Sprint 626 continued production hardening by tightening the manual-review ServiceNow work-note feedback path in `model_fulfillment.py`. Sprint 381 sanitized and bounded manual-review eligibility reasons, missing-context names, and reviewer notes, but the candidate metadata filters still used `isinstance(..., str)`, so string subclasses could be accepted as ordinary feedback text before work-note formatting.

Manual-review feedback now accepts only exact `str` instances from `eligibility_reasons` and `reviewer_notes`. String subclasses and non-string values are skipped before missing-context extraction, actionable reviewer-note selection, redaction, normalization, bounding, and ServiceNow work-note construction.

Verification:

- Added 1 failing-first model fulfillment test proving string subclass eligibility reasons and reviewer notes were accepted as normal feedback before implementation.
- `python3 -m pytest tests/test_model_fulfillment.py::test_model_fulfillment_manual_work_note_skips_string_subclass_metadata -q`: failed before implementation because subclassed metadata appeared in the work note.
- `python3 -m pytest tests/test_model_fulfillment.py -q`: 32 tests passed.
- `python3 -m pytest tests/test_model_fulfillment.py tests/test_project_docs.py::test_sprint_626_documents_manual_review_feedback_exact_string_boundary -q`: 33 tests passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 700 documentation tests passed.
- `python3 -m ruff check src tests`: passed.
- `python3 -m mypy src tests`: passed with no issues in 197 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2739 tests passed at 93.07% coverage.
