# Sprint 482 Change Log

## Build-claim structured artifact field sanitization

Hardened the build-claim writeback path so optional candidate artifact references cannot be written
raw into `u_ai_candidate_artifact` while a story is claimed for automated build orchestration.
Sprint 481 covered legacy external-build completion writebacks; this sprint closes the adjacent
claim-stage path that used the same ServiceNow field.

`plan_story_build_claim_writeback()` now routes `candidate_artifact_url` through the shared
structured writeback sanitizer before adding `u_ai_candidate_artifact` to planned fields. The
sanitizer redacts credential-like fragments, collapses whitespace/control characters, and caps the
value at 500 characters. State transition behavior and build-claim work-note behavior are unchanged.

## Verification

- Added 1 failing-first writeback test covering a secret-bearing, multiline build-claim candidate
  artifact reference.
- `python3 -m pytest tests/test_writeback.py::test_story_build_claim_structured_artifact_field_redacts_untrusted_value -q`:
  failed before implementation because the raw candidate artifact reference was planned into
  `u_ai_candidate_artifact`.
- `python3 -m pytest tests/test_writeback.py -q`: 14 tests passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 556 documentation tests passed.
- `python3 -m ruff check src tests`: passed.
- `python3 -m mypy src tests`: passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`:
  2407 total tests passed at 93.87% coverage.
