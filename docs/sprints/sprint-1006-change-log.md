# Sprint 1006 Change Log - Flow graph discovery record collection guard

## Summary

Hardened Flow Designer context discovery so fulfillment-flow resolution and read-only `flow_graph` retrieval validate live ServiceNow graph result containers before matching, citation construction, or graph record rendering.

## Security

`resolve_fulfillment_flow()`, `_flow_surfaces()`, and `_fetch_flow_graph_records()` now route `sys_hub_flow`, `sys_hub_trigger_instance`, `sys_hub_action_instance`, `sys_hub_flow_logic_instance_v2`, `sys_hub_trigger_input`, `sys_hub_trigger_output`, `sys_hub_action_input`, and `sys_hub_action_output` fetch results through the shared `_surface_records()` boundary.

The helper accepts only exact Python lists containing exact Python dictionaries and fails closed with `discovery text metadata contains non-JSON value`.

Malformed Flow graph containers fail before list truthiness, list iteration, `len()` hooks, record `.get()` hooks, fulfillment-flow matching, graph completeness checks, citation count calculation, graph record rendering, context dossier persistence, model invocation, ServiceNow import, or story writeback can consume caller-controlled container behavior.

## Tests

- Added 1 failing-first Flow graph record collection subclass assertion: `test_required_flow_graph_context_rejects_record_collection_subclass_without_leak`.
- Added 1 failing-first Flow graph record subclass assertion: `test_required_flow_graph_context_rejects_record_subclass_without_leak`.
- Added 1 documentation assertion: `test_sprint_1006_documents_flow_graph_discovery_record_collection_guard`.

## Verification

- `pytest tests/test_instance_discovery.py::test_required_flow_graph_context_rejects_record_collection_subclass_without_leak tests/test_instance_discovery.py::test_required_flow_graph_context_rejects_record_subclass_without_leak -q` failed before implementation because unsafe `len()` and record `.get()` hooks executed.
- `pytest tests/test_instance_discovery.py::test_required_flow_graph_context_rejects_record_collection_subclass_without_leak tests/test_instance_discovery.py::test_required_flow_graph_context_rejects_record_subclass_without_leak tests/test_instance_discovery.py::test_required_flow_graph_context_collects_graph_records_with_citations tests/test_instance_discovery.py::test_resolve_fulfillment_flow_returns_active_record_triggered_flow -q` - 4 passed.
