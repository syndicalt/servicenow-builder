"""CLI command implementations for ServiceNow writeback planning and verification."""

from __future__ import annotations

import argparse
from pathlib import Path

from jedi_devproject.artifacts import write_json_artifact_once, write_lifecycle_manifest
from jedi_devproject.cicd_update_sets import evaluate_cicd_update_set_capability
from jedi_devproject.cli_io import render_summary
from jedi_devproject.servicenow import ServiceNowClient, UrllibTransport
from jedi_devproject.writeback import ActorType, ExternalBuildStatus
from jedi_devproject.writeback_orchestration import (
    WritebackClient,
    WritebackExecutionRequest,
    WritebackExecutionResult,
    build_writeback_batch_report,
    evaluate_writeback_capability,
    execute_writeback,
    load_writeback_requests,
    run_writeback_batch,
    verify_writeback,
)


def _client_from_env(env_file: Path) -> ServiceNowClient:
    # Resolved through the CLI facade so patches against
    # jedi_devproject.cli.servicenow_client_from_env keep intercepting it.
    from jedi_devproject import cli

    return cli.servicenow_client_from_env(env_file, transport=UrllibTransport())


def plan_writeback_command(
    args: argparse.Namespace,
    parser: argparse.ArgumentParser,
) -> int:
    client = _client_from_env(args.env_file)
    if args.manifest_root is not None and (
        args.packet_path is None or args.candidate_path is None
    ):
        parser.error("plan-writeback --manifest-root requires --packet-path and --candidate-path")
    writeback_result = execute_writeback(
        client,
        WritebackExecutionRequest(
            story_number=args.story_number,
            build_reference=args.build_reference,
            artifact_url=args.artifact_url,
            build_status=ExternalBuildStatus(args.build_status),
            from_state=args.from_state,
            apply=args.apply,
            confirm_story_number=args.confirm_story_number,
            actor_type=ActorType(args.actor_type),
            actor_id=args.actor_id,
            execution_id=args.execution_id,
            audit_root=args.audit_root,
        ),
    )
    plan = writeback_result.plan
    printable_fields = " ".join(f"{key}={value}" for key, value in sorted(plan.fields.items()))
    printable_reasons = " ".join(
        f"reason={reason.replace(' ', '_')}"
        for reason in [*plan.reasons, *writeback_result.reasons]
    )
    print(
        f"dry_run=True story_number={plan.story_number} "
        f"allowed={plan.allowed} {printable_fields} {printable_reasons}".strip()
    )
    if writeback_result.applied:
        print(f"applied=True story_number={plan.story_number}")
        if args.manifest_root is not None:
            _write_apply_lifecycle_manifest(
                client=client,
                manifest_root=args.manifest_root,
                run_id=args.execution_id or args.build_reference,
                story_number=plan.story_number,
                build_reference=args.build_reference,
                artifact_url=args.artifact_url,
                packet_path=args.packet_path,
                candidate_path=args.candidate_path,
                candidate_batch_path=args.candidate_batch_path,
                writeback_result=writeback_result,
            )
    elif args.apply and writeback_result.reasons:
        print(f"applied=False reason={writeback_result.reasons[-1]}")
    return 0 if writeback_result.allowed and (not args.apply or writeback_result.applied) else 1


def check_writeback_capability_command(args: argparse.Namespace) -> int:
    client = _client_from_env(args.env_file)
    capability = evaluate_writeback_capability(client)
    missing_fields = ",".join(capability.missing_fields)
    reasons = ",".join(capability.reasons)
    print(
        f"allowed={capability.allowed} "
        f"ready_for_testing_state={capability.ready_for_testing_state} "
        f"missing_fields={missing_fields} reasons={reasons}"
    )
    return 0 if capability.allowed else 1


def check_cicd_update_set_capability_command(args: argparse.Namespace) -> int:
    client = _client_from_env(args.env_file)
    cicd_capability = evaluate_cicd_update_set_capability(client)
    probe_statuses = " ".join(
        f"{probe.action}_status={probe.status_code}" for probe in cicd_capability.probes
    )
    reasons = ",".join(cicd_capability.reasons)
    print(f"available={cicd_capability.available} {probe_statuses} reasons={reasons}")
    return 0 if cicd_capability.available else 1


def verify_writeback_command(args: argparse.Namespace) -> int:
    client = _client_from_env(args.env_file)
    verification = verify_writeback(
        client,
        story_number=args.story_number,
        build_reference=args.build_reference,
        artifact_url=args.artifact_url,
    )
    printable_fields = " ".join(
        f"{key}={value}" for key, value in sorted(verification.actual_fields.items())
    )
    printable_reasons = " ".join(f"reason={reason}" for reason in verification.reasons)
    print(
        f"verified={verification.verified} "
        f"story_number={verification.story_number} "
        f"expected_state={verification.expected_state} "
        f"{printable_fields} {printable_reasons}".strip()
    )
    return 0 if verification.verified else 1


def record_lifecycle_manifest_command(args: argparse.Namespace) -> int:
    manifest_path = write_lifecycle_manifest(
        args.manifest_root,
        run_id=args.run_id,
        story_number=args.story_number,
        build_reference=args.build_reference,
        packet_path=args.packet_path,
        candidate_path=args.candidate_path,
        writeback_audit_path=args.writeback_audit_path,
        verification={
            "verified": args.verification_verified,
            "expected_state": args.verification_state,
            "actual_fields": (
                {"state": args.verification_state} if args.verification_state is not None else {}
            ),
            "reasons": [] if args.verification_verified else ["not_verified"],
        },
    )
    print(f"lifecycle_manifest_written=True story_number={args.story_number} path={manifest_path}")
    return 0


def run_writeback_batch_command(args: argparse.Namespace) -> int:
    client = _client_from_env(args.env_file)
    requests = load_writeback_requests(
        args.jobs_file,
        apply=args.apply,
        actor_type=ActorType(args.actor_type),
        actor_id=args.actor_id,
        execution_id=args.execution_id,
        audit_root=args.audit_root,
    )
    batch = run_writeback_batch(client, requests)
    report_filename = f"{args.execution_id or 'writeback-batch'}.json"
    write_json_artifact_once(
        args.batch_report_root,
        filename=report_filename,
        payload=build_writeback_batch_report(
            batch,
            execution_id=args.execution_id,
            actor_id=args.actor_id,
        ),
    )
    print(render_summary(batch.summary))
    return 0 if batch.summary["blocked"] == 0 else 1


def _write_apply_lifecycle_manifest(
    *,
    client: WritebackClient,
    manifest_root: Path,
    run_id: str,
    story_number: str,
    build_reference: str,
    artifact_url: str | None,
    packet_path: Path | None,
    candidate_path: Path | None,
    candidate_batch_path: Path | None,
    writeback_result: WritebackExecutionResult,
) -> Path:
    if packet_path is None or candidate_path is None:
        raise ValueError("packet_path and candidate_path are required")
    verification = verify_writeback(
        client,
        story_number=story_number,
        build_reference=build_reference,
        artifact_url=artifact_url,
    )
    manifest_path = write_lifecycle_manifest(
        manifest_root,
        run_id=run_id,
        story_number=story_number,
        build_reference=build_reference,
        packet_path=packet_path,
        candidate_path=candidate_path,
        candidate_batch_path=candidate_batch_path,
        writeback_audit_path=writeback_result.audit_path,
        writeback={
            "allowed": writeback_result.allowed,
            "applied": writeback_result.applied,
            "idempotent": writeback_result.idempotent,
            "reasons": writeback_result.reasons or writeback_result.plan.reasons,
        },
        verification=verification.model_dump(mode="json"),
    )
    print(f"lifecycle_manifest_written=True story_number={story_number} path={manifest_path}")
    return manifest_path
