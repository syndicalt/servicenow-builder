# Sprint 1049 Change Log - Alert emission direct settings boundary

## Summary

Sprint 1049 continued production hardening by moving alert delivery settings validation into the direct worker alert emission boundary. `runtime_worker.main()` already loads and validates environment-backed alert settings, and `emit_alert_webhook()` still defends the low-level delivery primitive, but embedded worker callers could pass mutated `RuntimeSettings.alert_webhook_url` or `RuntimeSettings.alert_webhook_max_body_bytes` values directly into `_emit_worker_failure_alert()` and `_emit_stale_requeue_alert()`.

The direct worker alert emitters now validate the alert webhook URL and body-size limit before constructing alert payloads or invoking transport. Invalid direct settings fail as `RuntimeConfigError` diagnostics that name the runtime setting instead of leaking into URL helper `ValueError` or lower-level `AlertDeliveryError` paths after alert rendering.

## Changes

- Added `_alert_delivery_settings()` to normalize and validate direct `RuntimeSettings` alert delivery values.
- `_emit_worker_failure_alert()` and `_emit_stale_requeue_alert()` now reject URL string subclasses, malformed alert webhook URLs, non-integer body-size settings, non-positive body-size settings, and body-size settings above `65536` before alert construction or HTTP transport.
- Documented the direct worker alert emitter settings boundary in the operator guide.

## Tests

- Added 2 failing-first direct alert settings assertions:
  - `test_emit_worker_failure_alert_rejects_alert_url_subclass_before_transport`
  - `test_emit_stale_requeue_alert_rejects_invalid_body_limit_before_transport`
- Initial focused run failed before implementation because direct alert emitters surfaced URL helper `ValueError` and delivery `AlertDeliveryError` instead of `RuntimeConfigError`.
- Focused regression after implementation:
  - `pytest tests/test_runtime_worker_retention.py -q -k "emit_worker_failure_alert_rejects_alert_url_subclass or emit_stale_requeue_alert_rejects_invalid_body_limit"` - 2 passed.
