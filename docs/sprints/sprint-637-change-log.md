# Sprint 637 Change Log

## Model fulfillment persisted artifact exact-string boundary

Sprint 637 continued production hardening by tightening the model fulfillment helpers that turn persisted packet, candidate, and preflight artifacts into story-facing artifact references. The previous helpers used `str(artifact.path)` after artifacts were persisted, so malformed in-process artifact metadata could execute custom string conversion while retrieved Update Set handoff requests, human-review feedback, or flow preflight references were being prepared.

Model fulfillment now accepts only exact string persisted artifact paths before returning those references. Missing, non-string, string-subclass, or unstringifiable artifact path values fail closed with `persisted artifact path contains non-JSON value` before story work notes, structured AI fields, or retrieved Update Set handoff requests are created.

Verification:

- Added 1 failing-first model fulfillment test proving a hostile artifact path string subclass was accepted before implementation.
- `python3 -m pytest tests/test_model_fulfillment.py::test_model_fulfillment_rejects_persisted_artifact_path_subclass_without_leak -q`: failed before implementation because no `ValueError` was raised.
- `python3 -m pytest tests/test_model_fulfillment.py::test_model_fulfillment_rejects_persisted_artifact_path_subclass_without_leak tests/test_model_fulfillment.py::test_model_fulfillment_work_note_names_missing_surface_context tests/test_model_fulfillment.py::test_model_fulfillment_manual_work_note_sanitizes_reasons_and_reviewer_notes tests/test_model_fulfillment.py::test_model_fulfillment_manual_work_note_skips_string_subclass_metadata -q`: 4 tests passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 711 documentation tests passed.
- `python3 -m ruff check src tests`: passed.
- `python3 -m mypy src tests`: passed with no issues in 197 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2764 tests passed at 93.08% coverage.
