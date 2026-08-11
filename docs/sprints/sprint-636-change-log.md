# Sprint 636 Change Log

## Artifact manifest concrete Path boundary

Sprint 636 continued production hardening by tightening local artifact manifest path serialization. Lifecycle manifests, reviewed delivery lifecycle manifests, and delivery attachment audits persist local artifact path strings for audit review. Before this sprint, those writers converted accepted `Path` inputs with `str(path)`, which meant a corrupted in-process `Path` subclass could run custom string conversion while an audit manifest was being written.

Artifact manifest writers now route persisted path strings through a shared concrete-path boundary. Only the platform's concrete `pathlib.Path` type is accepted for serialized artifact paths. Path subclasses and other path-like objects fail closed with `artifact path must be a concrete pathlib Path` before manifest JSON is written or artifact hashes are calculated.

Verification:

- Added 2 failing-first artifact manifest tests proving hostile `Path` subclasses were accepted before implementation.
- `python3 -m pytest tests/test_writeback_audit.py::test_delivery_attachment_audit_rejects_path_subclass_without_leak -q`: failed before implementation because no `ArtifactWriteError` was raised.
- `python3 -m pytest tests/test_writeback_audit.py::test_delivery_attachment_audit_rejects_path_subclass_without_leak tests/test_writeback_audit.py::test_lifecycle_manifest_rejects_path_subclass_without_leak tests/test_writeback_audit.py::test_delivery_attachment_audit_is_write_once_without_story_sys_id tests/test_writeback_audit.py::test_write_lifecycle_manifest_ties_phase_artifacts_without_sys_ids tests/test_writeback_audit.py::test_lifecycle_manifest_hashes_artifacts_without_whole_file_read -q`: 5 tests passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 710 documentation tests passed.
- `python3 -m ruff check src tests`: passed.
- `python3 -m mypy src tests`: passed with no issues in 197 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2762 tests passed at 93.08% coverage.
