# Sprint 49 Change Log

## Delivery Contract Gate

- Added a `delivery_contract` gate to artifact handoff decisions.
- Required `delivery_contract=reviewed_export` before approved Update Set XML or test evidence can become ServiceNow delivery attachments.
- Kept `approved_for_delivery` as a required approval signal, but no longer sufficient by itself for live attachment.
- Changed `run-delivery-artifact-smoke` to emit `delivery_contract=smoke_placeholder` and zero planned ServiceNow attachments.
- Made `attach-delivery-artifacts` fail closed when a handoff report marks an artifact attachable without the reviewed export contract.
