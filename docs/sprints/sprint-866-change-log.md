# Sprint 866 Change Log

## ServiceNow empty field-list guard

- Added 1 failing-first ServiceNow empty field-list assertion covering explicit empty `fields` projections: `test_servicenow_client_rejects_empty_table_record_fields_before_request`.
- Implemented `ServiceNowClient.fetch_table_records(fields=...)` empty provided field-list rejection before request construction.

## Verification

- Focused red before implementation: `1 failed, 1 passed`; the ServiceNow assertion reached transport because explicit empty `fields=[]` was not rejected.
- Focused green after implementation: `2 passed in 0.19s`.
- ServiceNow suite: `295 passed in 0.27s`.
- Project docs suite: `939 passed in 0.60s`.
- Full coverage gate: `3430 passed in 9.00s`; total coverage `93.51%`.
