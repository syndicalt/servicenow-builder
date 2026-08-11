# Sprint 480 Change Log

## Advisory ATF test plan artifact non-finite number rejection

Hardened advisory ATF test plan artifact creation so corrupted in-process ATF plan DTOs cannot
silently attach `NaN`, `Infinity`, or `-Infinity` values to fulfillment artifacts. ATF plans are
review evidence, so they must follow the same strict JSON boundary as the context bundle,
implementation packet, and implementation candidate artifacts.

`_atf_test_plan_artifact()` now converts generated `AtfTestPlan` DTOs through the strict
`_model_artifact_payload()` preflight before adding an `atf_test_plan` artifact. Non-finite ATF
plan payloads fail with `ATF test plan artifact payload contains non-finite numeric values`, are
handled as advisory ATF generation failures, and cause the ATF plan artifact to be omitted while
the implementation candidate still completes. The diagnostic does not echo ATF step fields,
generated ATF values, story identifiers, or payload values.

## Verification

- Added 1 failing-first model fulfillment test covering a returned ATF plan with non-finite step
  input evidence without ATF field-name, value, or secret-bearing description reflection.
- `python3 -m pytest tests/test_model_fulfillment.py::test_model_candidate_handler_omits_atf_plan_when_payload_is_non_finite -q`:
  failed before implementation because the corrupted ATF plan was attached as an `atf_test_plan`
  artifact.
- `python3 -m pytest tests/test_model_fulfillment.py::test_model_candidate_handler_omits_atf_plan_when_payload_is_non_finite tests/test_model_fulfillment.py::test_model_candidate_handler_omits_atf_plan_when_generation_fails -q`:
  2 tests passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 554 documentation tests passed.
- `python3 -m ruff check src tests`: passed.
- `python3 -m mypy src tests`: passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`:
  2403 total tests passed at 93.87% coverage.
