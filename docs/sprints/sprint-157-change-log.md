# Sprint 157 Change Log

## Summary

- Added general automation feedback to non-automated story assessments. The feedback is not tied to a single ServiceNow domain; unsupported scope, missing details, point-limit routing, and other manual-review outcomes can all carry actionable operator guidance.
- Added a `suggested_story` rewrite to capability assessments so the fulfillment work note can tell the ServiceNow requester how to restate the story for a cleaner automated build, analysis-only recommendation, or manual developer route.
- Threaded feedback into manual-review candidates and ServiceNow work notes through `reviewer_notes`, preserving the existing candidate artifact and status workflow.
- Kept the behavior fail-closed: no retrieved Update Set is created just because rewrite guidance exists, and model invocation remains skipped when deterministic safety or context gates block generation.

## Verification

- `pytest tests/test_capability_analysis.py::test_non_automated_story_includes_general_rewrite_guidance tests/test_capability_analysis.py::test_missing_details_story_suggests_required_story_fields tests/test_model_fulfillment.py::test_model_fulfillment_work_note_includes_story_rewrite_guidance -q`
