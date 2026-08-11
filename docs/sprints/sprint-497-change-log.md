# Sprint 497 Change Log

## Intake feedback hash non-JSON value rejection

Hardened `_intake_content_hash()` so intake feedback provenance hashes cannot be minted over stringified runtime objects when corrupted in-process gate feedback contains unsupported Python values.

Sprint 471 rejected non-finite numeric intake feedback hash values. This sprint closes the adjacent structural JSON gap: unsupported objects, bytes, and other non-JSON values now fail before canonicalization or SHA-256 computation with the fixed `intake feedback hash payload contains non-JSON values` diagnostic. The diagnostic does not echo guidance field names, operator feedback, suggested rewrites, story identifiers, object type names, object string output, credential-like keys, or payload values.

The implementation validates the canonical hash payload before `json.dumps()` and reuses the same strict traversal used for capability assessment automation-intent payloads, keeping the assessment-stage JSON contracts aligned.

## Verification

- Added 1 failing-first capability assessment test proving an object with secret-bearing `__str__` output was previously accepted into the intake feedback hash input.
- `python3 -m pytest tests/test_capability_assessment.py::test_intake_feedback_hash_rejects_non_json_guidance_without_payload_leak -q`: failed before implementation because no `ValueError` was raised.
- `python3 -m pytest tests/test_capability_assessment.py::test_intake_feedback_hash_rejects_non_json_guidance_without_payload_leak tests/test_capability_assessment.py::test_intake_feedback_hash_rejects_non_finite_guidance_without_payload_leak tests/test_capability_assessment.py::test_build_intake_feedback_rejects_non_finite_guidance_without_payload_leak tests/test_capability_assessment.py::test_automation_intent_payload_rejects_non_json_value_without_leak tests/test_capability_assessment.py::test_automation_intent_payload_rejects_non_finite_numeric_value_without_leak -q`: 5 tests passed.
- `python3 -m pytest tests/test_capability_assessment.py -q`: 17 tests passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 571 documentation tests passed.
- `python3 -m ruff check src tests`: passed.
- `python3 -m mypy src tests`: passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2437 total tests passed at 93.74% coverage.
