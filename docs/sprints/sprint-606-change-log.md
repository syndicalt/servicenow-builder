# Sprint 606 Change Log

## Writeback batch report diagnostic key collision preservation

Sprint 606 continued production hardening by preserving every diagnostic entry in writeback batch reports when sanitized dictionary keys collide. Sprint 605 made diagnostic keys safe by avoiding `str()` and `repr()` on malformed non-string keys, but duplicate rendered keys could still overwrite earlier entries after projection. That was an auditability gap: a report could silently lose evidence when multiple non-JSON keys rendered as `[non-json key]` or multiple secret-bearing string keys redacted to the same sanitized value.

`_diagnostic_report_node()` now projects dictionaries with an explicit insertion loop. `_deduplicated_diagnostic_report_key()` preserves the first rendered key unchanged and gives later collisions deterministic `[duplicate N]` suffixes. `_duplicate_diagnostic_report_key()` keeps suffixed keys inside the same bounded work-note field-value envelope by truncating the prefix before appending the duplicate suffix when needed.

Verification:

- Added 1 failing-first writeback batch report collision-preservation test proving duplicate rendered diagnostic keys overwrote earlier evidence before implementation.
- `python3 -m pytest tests/test_writeback_orchestration.py::test_build_writeback_batch_report_preserves_colliding_diagnostic_keys -q`: failed before implementation because `[non-json key]` contained the second diagnostic and the first diagnostic was lost.
- `python3 -m pytest tests/test_writeback_orchestration.py::test_build_writeback_batch_report_preserves_colliding_diagnostic_keys tests/test_writeback_orchestration.py::test_build_writeback_batch_report_normalizes_non_string_diagnostic_keys -q`: 2 passed.
- `python3 -m pytest tests/test_project_docs.py::test_sprint_606_documents_writeback_batch_report_key_collision_preservation tests/test_project_docs.py::test_sprint_605_documents_writeback_batch_report_diagnostic_key_projection -q`: 2 passed.
- `python3 -m pytest tests/test_writeback_orchestration.py -q`: 26 passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 680 passed.
- `python3 -m ruff check src tests`: all checks passed.
- `python3 -m mypy src tests`: success, no issues found in 196 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2690 passed, total coverage 93.15%, required 90% coverage reached.
