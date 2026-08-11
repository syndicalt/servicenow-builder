# Sprint 867 Change Log

## ServiceNow CI/CD request-container truthiness guard

- Added 2 failing-first ServiceNow CI/CD request-container truthiness assertions: `test_servicenow_client_rejects_cicd_request_params_before_truthiness` and `test_servicenow_client_rejects_cicd_request_body_before_truthiness`.
- Implemented `ServiceNowClient._send_cicd_update_set_request()` optional params and body exact-dictionary validation before request construction or truthiness branching.

## Verification

- Focused red before implementation: `2 failed, 1 passed`; both ServiceNow assertions reached hostile container `__bool__` hooks from `params or {}` and `body or {}`.
- Focused green after implementation: `3 passed in 0.21s`.
- ServiceNow suite: `297 passed in 0.28s`.
- Project docs suite: `940 passed in 0.60s`.
- Full coverage gate: `3433 passed in 9.55s`; total coverage `93.52%`.
