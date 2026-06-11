"""CLI command implementations for ServiceNow bootstrap planning and verification."""

from __future__ import annotations

import argparse
from pathlib import Path

from pydantic import ValidationError

from jedi_devproject.artifacts import write_json_artifact_once
from jedi_devproject.bootstrap import (
    LifecycleWebhookBootstrapSpec,
    UpdateSetImporterBootstrapSpec,
    apply_bootstrap_fields,
    apply_lifecycle_webhook_records,
    apply_update_set_importer_records,
    build_lifecycle_webhook_bootstrap_spec,
    build_update_set_importer_bootstrap_spec,
    lifecycle_webhook_servicenow_record_plan,
    plan_bootstrap_fields,
    update_set_importer_servicenow_record_plan,
    verify_lifecycle_webhook_records,
    verify_update_set_importer_records,
)
from jedi_devproject.cli_io import load_json_object
from jedi_devproject.servicenow import ServiceNowClient, UrllibTransport


def _client_from_env(env_file: Path) -> ServiceNowClient:
    # Resolved through the CLI facade so patches against
    # jedi_devproject.cli.servicenow_client_from_env keep intercepting it.
    from jedi_devproject import cli

    return cli.servicenow_client_from_env(env_file, transport=UrllibTransport())


def plan_bootstrap_fields_command(args: argparse.Namespace) -> int:
    client = _client_from_env(args.env_file)
    bootstrap_plan = plan_bootstrap_fields(client.fetch_story_dictionary_fields())
    missing_fields = ",".join(bootstrap_plan.missing_fields)
    print(
        f"ready={bootstrap_plan.ready} table={bootstrap_plan.table} "
        f"missing_fields={missing_fields} "
        f"fields_to_create={len(bootstrap_plan.fields_to_create)} "
        f"fields_to_update_writable={len(bootstrap_plan.fields_to_update_writable)} "
        f"form_layout_changes={len(bootstrap_plan.form_layout_changes)}"
    )
    return 0 if bootstrap_plan.ready else 1


def apply_bootstrap_fields_command(args: argparse.Namespace) -> int:
    client = _client_from_env(args.env_file)
    bootstrap_result = apply_bootstrap_fields(
        client,
        confirm_table=args.confirm_table,
        confirm_fields=args.confirm_fields,
    )
    audit_payload = bootstrap_result.model_dump(mode="json")
    audit_payload["run_id"] = args.run_id
    write_json_artifact_once(
        args.audit_root,
        filename=f"{args.run_id}.json",
        payload=audit_payload,
    )
    reasons = " ".join(f"reason={reason}" for reason in bootstrap_result.reasons)
    print(
        f"applied={bootstrap_result.applied} "
        f"created_fields={len(bootstrap_result.created_fields)} "
        f"updated_writable_fields={len(bootstrap_result.updated_writable_fields)} "
        f"platform_readonly_records={len(bootstrap_result.platform_readonly_records)} "
        f"form_layout_changes={len(bootstrap_result.form_layout_changes)} "
        f"{reasons}".strip()
    )
    return 0 if bootstrap_result.applied or not bootstrap_result.reasons else 1


def plan_lifecycle_business_rule_command(args: argparse.Namespace) -> int:
    try:
        webhook_bootstrap_spec = build_lifecycle_webhook_bootstrap_spec(
            endpoint_url=args.endpoint_url,
            integration_identity=args.integration_identity,
            draft_state_value=args.draft_state_value,
            ready_state_value=args.ready_state_value,
            ready_for_testing_state_value=args.ready_for_testing_state_value,
            complete_state_value=args.complete_state_value,
            hmac_secret_property_name=args.hmac_secret_property_name,
        )
    except ValueError as exc:
        print(f"lifecycle_business_rule_specs=0 reason={exc}")
        return 1
    spec_path = write_json_artifact_once(
        args.spec_root,
        filename=f"{args.run_id}.json",
        payload={
            **webhook_bootstrap_spec.model_dump(mode="json"),
            "servicenow_records": lifecycle_webhook_servicenow_record_plan(webhook_bootstrap_spec),
        },
    )
    print(
        "lifecycle_business_rule_specs=1 "
        f"table={webhook_bootstrap_spec.business_rule.table} "
        f"rest_message={webhook_bootstrap_spec.rest_message.name} "
        f"path={spec_path}"
    )
    return 0


def plan_update_set_importer_command(args: argparse.Namespace) -> int:
    try:
        importer_spec = build_update_set_importer_bootstrap_spec(
            integration_identity=args.integration_identity,
        )
    except ValueError as exc:
        print(f"update_set_importer_specs=0 reason={exc}")
        return 1
    spec_path = write_json_artifact_once(
        args.spec_root,
        filename=f"{args.run_id}.json",
        payload={
            **importer_spec.model_dump(mode="json"),
            "servicenow_records": update_set_importer_servicenow_record_plan(importer_spec),
        },
    )
    print(
        "update_set_importer_specs=1 "
        f"service_id={importer_spec.definition.service_id} "
        f"path={spec_path}"
    )
    return 0


def apply_lifecycle_webhook_command(args: argparse.Namespace) -> int:
    try:
        spec = LifecycleWebhookBootstrapSpec.model_validate(load_json_object(args.spec_file))
    except (ValidationError, ValueError) as exc:
        print(
            f"lifecycle_webhook_applied=False reason=invalid_lifecycle_webhook_spec detail={exc}"
        )
        return 1
    client = _client_from_env(args.env_file)
    lifecycle_apply_result = apply_lifecycle_webhook_records(
        client,
        spec=spec,
        confirm_table=args.confirm_table,
        confirm_records=args.confirm_records,
    )
    if lifecycle_apply_result.applied:
        write_json_artifact_once(
            args.audit_root,
            filename=f"{args.run_id}.json",
            payload=lifecycle_apply_result.model_dump(mode="json"),
        )
    reasons = " ".join(f"reason={reason}" for reason in lifecycle_apply_result.reasons)
    print(
        f"lifecycle_webhook_applied={lifecycle_apply_result.applied} "
        f"upserted_records={len(lifecycle_apply_result.upserted_records)} "
        f"{reasons}".strip()
    )
    return 0 if lifecycle_apply_result.applied or not lifecycle_apply_result.reasons else 1


def apply_update_set_importer_command(args: argparse.Namespace) -> int:
    try:
        importer_spec = UpdateSetImporterBootstrapSpec.model_validate(
            load_json_object(args.spec_file)
        )
    except (ValidationError, ValueError) as exc:
        print(
            "update_set_importer_applied=False "
            f"reason=invalid_update_set_importer_spec detail={exc}"
        )
        return 1
    client = _client_from_env(args.env_file)
    importer_apply_result = apply_update_set_importer_records(
        client,
        spec=importer_spec,
        confirm_service_id=args.confirm_service_id,
        confirm_records=args.confirm_records,
    )
    if importer_apply_result.applied:
        write_json_artifact_once(
            args.audit_root,
            filename=f"{args.run_id}.json",
            payload=importer_apply_result.model_dump(mode="json"),
        )
    reasons = " ".join(f"reason={reason}" for reason in importer_apply_result.reasons)
    print(
        f"update_set_importer_applied={importer_apply_result.applied} "
        f"upserted_records={len(importer_apply_result.upserted_records)} "
        f"{reasons}".strip()
    )
    return 0 if importer_apply_result.applied or not importer_apply_result.reasons else 1


def verify_lifecycle_webhook_command(args: argparse.Namespace) -> int:
    try:
        spec = LifecycleWebhookBootstrapSpec.model_validate(load_json_object(args.spec_file))
    except (ValidationError, ValueError) as exc:
        print(
            f"lifecycle_webhook_verified=False reason=invalid_lifecycle_webhook_spec detail={exc}"
        )
        return 1
    client = _client_from_env(args.env_file)
    lifecycle_webhook_verification = verify_lifecycle_webhook_records(
        client,
        spec=spec,
    )
    report_path = write_json_artifact_once(
        args.report_root,
        filename=f"{args.run_id}.json",
        payload=lifecycle_webhook_verification.model_dump(mode="json"),
    )
    reasons = " ".join(f"reason={reason}" for reason in lifecycle_webhook_verification.reasons)
    print(
        f"lifecycle_webhook_verified={lifecycle_webhook_verification.verified} "
        f"matched_records={len(lifecycle_webhook_verification.matched_records)} "
        f"missing_records={len(lifecycle_webhook_verification.missing_records)} "
        f"path={report_path} "
        f"{reasons}".strip()
    )
    return 0 if lifecycle_webhook_verification.verified else 1


def verify_update_set_importer_command(args: argparse.Namespace) -> int:
    try:
        importer_spec = UpdateSetImporterBootstrapSpec.model_validate(
            load_json_object(args.spec_file)
        )
    except (ValidationError, ValueError) as exc:
        print(
            "update_set_importer_verified=False "
            f"reason=invalid_update_set_importer_spec detail={exc}"
        )
        return 1
    client = _client_from_env(args.env_file)
    importer_verification = verify_update_set_importer_records(
        client,
        spec=importer_spec,
    )
    report_path = write_json_artifact_once(
        args.report_root,
        filename=f"{args.run_id}.json",
        payload=importer_verification.model_dump(mode="json"),
    )
    reasons = " ".join(f"reason={reason}" for reason in importer_verification.reasons)
    print(
        f"update_set_importer_verified={importer_verification.verified} "
        f"matched_records={len(importer_verification.matched_records)} "
        f"missing_records={len(importer_verification.missing_records)} "
        f"path={report_path} "
        f"{reasons}".strip()
    )
    return 0 if importer_verification.verified else 1
