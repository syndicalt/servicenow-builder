# Sprint 64 Change Log

## Lifecycle Webhook Bootstrap Bundle

- Refactored lifecycle bootstrap planning into a `Lifecycle webhook bootstrap bundle`.
- Added an Outbound REST Message spec named `Jedi DevProject Lifecycle Event API` with method `post_event`.
- Changed `plan-lifecycle-business-rule` output to include both `rest_message` and `business_rule` sections.
- Kept the endpoint URL out of the Business Rule script so transport configuration and authentication remain governed in ServiceNow.
- Marked REST Message authentication as `configured_in_servicenow`; no credential material is generated or stored in artifacts.
- Kept `story_sys_id` out of both the Business Rule payload and the bootstrap artifact.

## Verification

- Updated bootstrap tests so the Business Rule references the named REST Message/method instead of embedding the endpoint.
- Added tests for the combined REST Message plus Business Rule bootstrap spec.
- Updated CLI tests for the new bundled artifact shape.
- Updated operator documentation for the trigger/transport separation.
