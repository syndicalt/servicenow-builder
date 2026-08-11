# Sprint 870 Change Log

## ServiceNow missing response result guard

- Added 2 failing-first ServiceNow missing result assertions: `test_servicenow_result_record_list_rejects_missing_result_without_silent_empty` and `test_servicenow_result_object_rejects_missing_result_without_silent_empty`.
- Implemented shared ServiceNow successful-response result helper rejection for missing `result` keys before list or object shape defaults can turn malformed upstream responses into silent empty successes.

## Verification

- Focused red before implementation: `2 failed, 1 passed`; successful responses without `result` silently became empty list/object successes.
- Focused green after implementation: `3 passed in 0.19s`.
- ServiceNow suite: `304 passed in 0.26s`.
- Project docs suite after preserving historical documentation anchors: `943 passed in 0.58s`.
- Full coverage gate: `3443 passed in 9.11s`; total coverage `93.53%`.
