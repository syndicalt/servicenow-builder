# Sprint 471 Change Log

## Intake feedback content hash non-finite number rejection

Hardened intake feedback content hashing so gate-failure guidance provenance cannot be minted over
non-strict JSON containing `NaN`, `Infinity`, or `-Infinity`. Intake feedback artifacts and work
notes are used to explain why a story needs clarification or human review, so their content hashes
must fail closed if corrupted in-process guidance reaches the hash boundary.

`_intake_content_hash()` now serializes with strict JSON numeric handling before SHA-256
computation. Non-finite intake feedback hash payloads fail with
`intake feedback hash payload contains non-finite numeric values`. The diagnostic is stable and does
not echo operator feedback, suggested rewrites, story identifiers, field names, or values.

## Verification

- Added 2 failing-first capability assessment tests covering direct content-hash non-finite rejection
  and public intake feedback behavior without payload reflection.
- `python3 -m pytest tests/test_capability_assessment.py::test_intake_feedback_hash_rejects_non_finite_guidance_without_payload_leak -q`:
  failed before implementation because `_intake_content_hash()` accepted `NaN`.
- `python3 -m pytest tests/test_capability_assessment.py::test_intake_feedback_hash_rejects_non_finite_guidance_without_payload_leak tests/test_capability_assessment.py::test_build_intake_feedback_rejects_non_finite_guidance_without_payload_leak tests/test_capability_assessment.py::test_content_hash_is_deterministic_and_content_sensitive -q`:
  3 tests passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 545 documentation tests passed.
- `python3 -m ruff check src tests`: passed.
- `python3 -m mypy src tests`: passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`:
  2385 total tests passed at 93.84% coverage.
