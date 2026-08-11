# Sprint 869 Change Log

## ServiceNow empty lookup body guard

- Added 2 failing-first ServiceNow empty lookup assertions: `test_servicenow_client_rejects_empty_lookup_before_request` and `test_servicenow_client_rejects_empty_upsert_lookup_before_lookup`.
- Implemented `ServiceNowClient.fetch_table_record()` and `ServiceNowClient.upsert_table_record()` empty lookup rejection before OAuth token acquisition, query construction, upsert lookup decisions, mutation construction, or Table API transport.
- Preserved explicit bounded list scans for `ServiceNowClient.fetch_table_records(lookup={...})`; empty lookup dictionaries remain allowed only for list retrieval paths with a validated `sysparm_limit`.

## Verification

- Focused red before implementation: `2 failed, 1 passed`; empty point lookups reached OAuth token acquisition.
- Initial full coverage gate after the first shared-helper implementation: `2 failed, 3437 passed`; runtime integration tests exposed legitimate bounded list scans that use `fetch_table_records(lookup={})`.
- Refined focused green after preserving bounded list scans: `6 passed in 0.73s`.
- ServiceNow suite: `302 passed in 0.28s`.
- Runtime suite: `420 passed in 1.44s`.
- Project docs suite: `942 passed in 0.64s`.
- Full coverage gate: `3440 passed in 9.67s`; total coverage `93.52%`.
