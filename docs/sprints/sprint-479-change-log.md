# Sprint 479 Change Log

## Capability assessment automation-intent non-finite number rejection

Hardened capability assessment construction so normalized `AutomationIntent` DTOs cannot silently
embed corrupted in-process numeric values containing `NaN`, `Infinity`, or `-Infinity` into
`StoryCapabilityAssessment.automation_intent`. This closes the assessment-stage boundary before
implementation packets, model prompts, or persisted artifacts see the normalized intent payload.

`_automation_intent_payload()` now preflights Python-mode automation intent payloads with strict JSON
numeric handling before returning the established JSON-mode shape. Non-finite automation-intent
payloads fail with `automation intent payload contains non-finite numeric values`. The diagnostic is
stable and does not echo intent field names, field labels, story identifiers, or payload values.

## Verification

- Added 1 failing-first capability assessment test covering a non-finite automation intent
  `max_length` value without field-name, field-label, or value reflection.
- `python3 -m pytest tests/test_capability_assessment.py::test_automation_intent_payload_rejects_non_finite_numeric_value_without_leak -q`:
  failed before implementation because `_automation_intent_payload()` did not exist and capability
  assessments used direct JSON-mode intent dumps.
- `python3 -m pytest tests/test_capability_assessment.py::test_automation_intent_payload_rejects_non_finite_numeric_value_without_leak tests/test_capability_assessment.py::test_build_intake_feedback_rejects_non_finite_guidance_without_payload_leak tests/test_capability_assessment.py::test_missing_detail_feedback_has_stable_codes_and_capability_guidance -q`:
  3 tests passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 553 documentation tests passed.
- `python3 -m ruff check src tests`: passed.
- `python3 -m mypy src tests`: passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`:
  2401 total tests passed at 93.87% coverage.
