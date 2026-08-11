# Sprint 868 Change Log

## ServiceNow CI/CD request method/action guard

- Added 2 failing-first ServiceNow CI/CD request method/action assertions: `test_servicenow_client_rejects_cicd_request_method_before_auth` and `test_servicenow_client_rejects_cicd_request_action_before_url_construction`.
- Implemented `ServiceNowClient._send_cicd_update_set_request()` CI/CD request method and action validation before OAuth token acquisition, URL construction, request construction, or transport.

## Verification

- Focused red before implementation: `2 failed, 1 passed`; the unsafe method reached OAuth token acquisition, and the hostile action string subclass executed during URL interpolation.
- Focused green after implementation: `3 passed in 0.18s`.
- ServiceNow suite: `299 passed in 0.26s`.
- Project docs suite: `941 passed in 0.65s`.
- Full coverage gate: `3436 passed in 9.02s`; total coverage `93.52%`.
