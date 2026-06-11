"""Update Set importer bootstrap: scripted REST API spec, plan, apply, and verification."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from jedi_devproject.bootstrap_lifecycle import (
    LifecycleWebhookClient,
    LifecycleWebhookReadClient,
    LifecycleWebhookVerificationResult,
    _js_string,
    _mismatched_fields,
    _require_non_empty,
)


class UpdateSetImporterApplyResult(BaseModel):
    applied: bool
    upserted_records: list[dict[str, Any]]
    reasons: list[str]


class UpdateSetImporterDefinitionSpec(BaseModel):
    name: str
    service_id: str
    active: bool
    consumes: str
    produces: str
    short_description: str


class UpdateSetImporterOperationSpec(BaseModel):
    name: str
    http_method: str
    active: bool
    consumes: str
    produces: str
    requires_authentication: bool
    requires_acl_authorization: bool
    short_description: str
    operation_script: str


class UpdateSetImporterBootstrapSpec(BaseModel):
    definition: UpdateSetImporterDefinitionSpec
    operation: UpdateSetImporterOperationSpec


def build_update_set_importer_bootstrap_spec(
    *,
    integration_identity: str,
) -> UpdateSetImporterBootstrapSpec:
    _require_non_empty("integration_identity", integration_identity)
    definition = UpdateSetImporterDefinitionSpec(
        name="Jedi DevProject Update Set Import API",
        service_id="jedi_update_set_import",
        active=True,
        consumes="application/json",
        produces="application/json",
        short_description=(
            "Imports reviewed Jedi DevProject Update Set XML into retrieved update sets."
        ),
    )
    operation = UpdateSetImporterOperationSpec(
        name="import_update_set_xml",
        http_method="POST",
        active=True,
        consumes="application/json",
        produces="application/json",
        requires_authentication=True,
        requires_acl_authorization=True,
        short_description="Import reviewed Update Set XML using GlideUpdateManager2.",
        operation_script=_update_set_importer_operation_script(
            integration_identity=integration_identity
        ),
    )
    return UpdateSetImporterBootstrapSpec(definition=definition, operation=operation)


def update_set_importer_servicenow_record_plan(
    spec: UpdateSetImporterBootstrapSpec,
) -> list[dict[str, Any]]:
    return [
        {
            "table": "sys_ws_definition",
            "operation": "insert_or_update",
            "lookup": {"service_id": spec.definition.service_id},
            "fields": {
                "name": spec.definition.name,
                "service_id": spec.definition.service_id,
                "active": spec.definition.active,
                "consumes": spec.definition.consumes,
                "produces": spec.definition.produces,
                "short_description": spec.definition.short_description,
            },
        },
        {
            "table": "sys_ws_operation",
            "operation": "insert_or_update",
            "lookup": {
                "web_service_definition_name": spec.definition.name,
                "name": spec.operation.name,
            },
            "fields": {
                "name": spec.operation.name,
                "http_method": spec.operation.http_method,
                "active": spec.operation.active,
                "consumes": spec.operation.consumes,
                "produces": spec.operation.produces,
                "requires_authentication": spec.operation.requires_authentication,
                "requires_acl_authorization": spec.operation.requires_acl_authorization,
                "short_description": spec.operation.short_description,
                "operation_script": spec.operation.operation_script,
            },
        },
    ]


def apply_update_set_importer_records(
    client: LifecycleWebhookClient,
    *,
    spec: UpdateSetImporterBootstrapSpec,
    confirm_service_id: str | None,
    confirm_records: bool,
) -> UpdateSetImporterApplyResult:
    if confirm_service_id != spec.definition.service_id or not confirm_records:
        return UpdateSetImporterApplyResult(
            applied=False,
            upserted_records=[],
            reasons=["update_set_importer_confirmation_required"],
        )

    upserted_records: list[dict[str, Any]] = []
    for record in _update_set_importer_apply_records(
        spec,
        web_service_definition_sys_id=None,
    ):
        result = client.upsert_table_record(
            table=str(record["table"]),
            lookup=record["lookup"],
            fields=record["fields"],
        )
        upserted_records.append(
            {
                "table": record["table"],
                "lookup": record["lookup"],
                "sys_id": result.get("sys_id"),
            }
        )
        if record["table"] != "sys_ws_definition":
            continue
        definition_sys_id = str(result.get("sys_id") or "")
        if not definition_sys_id:
            continue
        for operation_record in _update_set_importer_apply_records(
            spec,
            web_service_definition_sys_id=definition_sys_id,
        ):
            if operation_record["table"] != "sys_ws_operation":
                continue
            operation_result = client.upsert_table_record(
                table=str(operation_record["table"]),
                lookup=operation_record["lookup"],
                fields=operation_record["fields"],
            )
            upserted_records.append(
                {
                    "table": operation_record["table"],
                    "lookup": operation_record["lookup"],
                    "sys_id": operation_result.get("sys_id"),
                }
            )
        break

    return UpdateSetImporterApplyResult(
        applied=bool(upserted_records),
        upserted_records=upserted_records,
        reasons=[],
    )


def verify_update_set_importer_records(
    client: LifecycleWebhookReadClient,
    *,
    spec: UpdateSetImporterBootstrapSpec,
) -> LifecycleWebhookVerificationResult:
    matched_records: list[str] = []
    missing_records: list[str] = []
    mismatched_fields: dict[str, list[str]] = {}
    definition_record = client.fetch_table_record(
        table="sys_ws_definition",
        lookup={"service_id": spec.definition.service_id},
    )
    definition_plan = update_set_importer_servicenow_record_plan(spec)[0]
    if definition_record is None:
        missing_records.append("sys_ws_definition")
    else:
        mismatches = _mismatched_fields(definition_record, definition_plan["fields"])
        if mismatches:
            mismatched_fields["sys_ws_definition"] = mismatches
        else:
            matched_records.append("sys_ws_definition")

    definition_sys_id = str((definition_record or {}).get("sys_id") or "")
    if definition_sys_id:
        operation_record = client.fetch_table_record(
            table="sys_ws_operation",
            lookup={
                "web_service_definition": definition_sys_id,
                "name": spec.operation.name,
            },
        )
        operation_plan = _update_set_importer_verification_records(
            spec,
            web_service_definition_sys_id=definition_sys_id,
        )[0]
        if operation_record is None:
            missing_records.append("sys_ws_operation")
        else:
            operation_mismatches = _mismatched_fields(
                operation_record,
                operation_plan["fields"],
            )
            if operation_mismatches:
                mismatched_fields["sys_ws_operation"] = operation_mismatches
            else:
                matched_records.append("sys_ws_operation")
    else:
        missing_records.append("sys_ws_operation")

    reasons: list[str] = []
    if missing_records:
        reasons.append("record_missing")
    if mismatched_fields:
        reasons.append("field_mismatch")
    return LifecycleWebhookVerificationResult(
        verified=not reasons,
        matched_records=matched_records,
        missing_records=missing_records,
        mismatched_fields=mismatched_fields,
        reasons=reasons,
    )


def _update_set_importer_apply_records(
    spec: UpdateSetImporterBootstrapSpec,
    *,
    web_service_definition_sys_id: str | None,
) -> list[dict[str, Any]]:
    plan = update_set_importer_servicenow_record_plan(spec)
    if web_service_definition_sys_id is None:
        return [record for record in plan if record["table"] == "sys_ws_definition"]
    operation = [record for record in plan if record["table"] == "sys_ws_operation"][0]
    return [
        {
            **operation,
            "lookup": {
                "web_service_definition": web_service_definition_sys_id,
                "name": spec.operation.name,
            },
            "fields": {
                **operation["fields"],
                "web_service_definition": web_service_definition_sys_id,
            },
        }
    ]


def _update_set_importer_verification_records(
    spec: UpdateSetImporterBootstrapSpec,
    *,
    web_service_definition_sys_id: str,
) -> list[dict[str, Any]]:
    return _update_set_importer_apply_records(
        spec,
        web_service_definition_sys_id=web_service_definition_sys_id,
    )


def _update_set_importer_operation_script(*, integration_identity: str) -> str:
    return f"""(function process(request, response) {{
    var body = request.body && request.body.data ? request.body.data : {{}};
    var xmlPayload = body.update_set_xml;
    if (!xmlPayload || typeof xmlPayload !== 'string') {{
        response.setStatus(400);
        response.setBody({{
            status: 'failed',
            reason: 'update_set_xml_required'
        }});
        return;
    }}

    var trimmedXml = xmlPayload.replace(/^\\s+|\\s+$/g, '');
    trimmedXml = trimmedXml.replace(/^<\\?xml[^>]*>/, '').replace(/^\\s+|\\s+$/g, '');
    if (trimmedXml.indexOf('<unload') !== 0) {{
        response.setStatus(400);
        response.setBody({{
            status: 'failed',
            reason: 'invalid_update_set_xml'
        }});
        return;
    }}

    var updateManager = new GlideUpdateManager2();
    var loadResult = updateManager.loadXML(xmlPayload);
    response.setStatus(201);
    response.setBody({{
        status: 'imported',
        imported_by: {_js_string(integration_identity)},
        load_result: loadResult ? loadResult.toString() : ''
    }});
}})(request, response);"""
