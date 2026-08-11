# Sprint 481 Change Log

## Legacy external-build structured writeback field sanitization

Hardened the legacy external-build writeback path so untrusted build references and candidate
artifact references cannot be written raw into visible ServiceNow automation metadata fields.
Work notes were already sanitized, but `u_ai_build_reference` and `u_ai_candidate_artifact` were
still planned from raw `ExternalBuildResult` values.

`_base_fields()` now routes `build_reference` and `artifact_url` through the same bounded redaction
used for write-note fragments before returning planned structured fields. This redacts
credential-like fragments, collapses whitespace/control characters, and caps each planned legacy
field value at 500 characters. The retrieved Update Set handoff metadata path is unchanged.

## Verification

- Added 1 failing-first writeback test covering secret-bearing and multiline legacy structured
  writeback values.
- `python3 -m pytest tests/test_writeback.py::test_external_build_structured_fields_redact_and_normalize_untrusted_values -q`:
  failed before implementation because the raw build reference was planned into
  `u_ai_build_reference`.
- `python3 -m pytest tests/test_writeback.py -q`: 13 tests passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 555 documentation tests passed.
- `python3 -m ruff check src tests`: passed.
- `python3 -m mypy src tests`: passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`:
  2405 total tests passed at 93.87% coverage.
