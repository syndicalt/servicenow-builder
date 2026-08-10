"""CLI entry point: argument parsing, command dispatch, and the public facade.

Command implementations live in the ``cli_pipeline``, ``cli_writeback``,
``cli_delivery``, and ``cli_bootstrap`` modules. This module keeps ``main``
and re-exports the historical public API (including patch targets such as
``jedi_devproject.cli.servicenow_client_from_env``).
"""

from __future__ import annotations

import argparse
from pathlib import Path

from pydantic import ValidationError

from jedi_devproject import __version__
from jedi_devproject.artifact_handoff import (
    ArtifactKind,
    build_artifact_handoff_report,
    build_artifact_handoff_work_note,
    build_reviewed_delivery_artifact_job,
    delivery_attachment_jobs_from_report,
)
from jedi_devproject.artifacts import (
    write_candidate_artifact,
    write_delivery_attachment_audit,
    write_json_artifact_once,
    write_lifecycle_manifest,
    write_reviewed_delivery_lifecycle_manifest,
)
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
from jedi_devproject.cicd_update_sets import evaluate_cicd_update_set_capability
from jedi_devproject.cli_bootstrap import (
    apply_bootstrap_fields_command,
    apply_lifecycle_webhook_command,
    apply_update_set_importer_command,
    plan_bootstrap_fields_command,
    plan_lifecycle_business_rule_command,
    plan_update_set_importer_command,
    verify_lifecycle_webhook_command,
    verify_update_set_importer_command,
)
from jedi_devproject.cli_delivery import (
    attach_delivery_artifacts_command,
    plan_artifact_handoff_command,
    process_external_build_result_command,
    process_lifecycle_event_command,
    review_delivery_artifact_command,
    run_delivery_artifact_smoke_command,
    run_reviewed_delivery_smoke_command,
    write_artifact_handoff_summary_command,
)
from jedi_devproject.cli_pipeline import (
    StaticResponseProvider,
    build_implementation_candidate_command,
    build_implementation_packet_command,
    run_implementation_candidates_command,
    run_lifecycle_smoke_command,
    run_local_command,
    run_pdi_command,
)
from jedi_devproject.cli_writeback import (
    check_cicd_update_set_capability_command,
    check_writeback_capability_command,
    plan_writeback_command,
    record_lifecycle_manifest_command,
    run_writeback_batch_command,
    verify_writeback_command,
)
from jedi_devproject.external_build import (
    ExternalBuildPipelineResult,
    reviewed_delivery_jobs_from_build_result,
    writeback_job_from_build_result,
)
from jedi_devproject.implementation_packet import (
    IMPLEMENTATION_PACKET_TASK,
    build_implementation_packet,
    generate_implementation_update_set_candidate_from_packet,
)
from jedi_devproject.instance_discovery import (
    DiscoveredField,
    DiscoveredFormElement,
    DiscoveredFormSection,
    InstanceDiscoveryContext,
)
from jedi_devproject.lifecycle_events import (
    LifecycleStateChangeEvent,
    plan_story_ready_lifecycle_event,
)
from jedi_devproject.models import (
    DataClassification,
    ProviderPolicy,
    ProviderStatus,
    Story,
    UpdateSetCandidate,
)
from jedi_devproject.operational_store import connect_operational_store
from jedi_devproject.pipeline import PipelineInputs, run_pipeline
from jedi_devproject.rag import Document, RagDomain, SpecializedRags
from jedi_devproject.runtime_config import load_runtime_settings
from jedi_devproject.safety import AllowlistPolicy, StoryType
from jedi_devproject.servicenow import UrllibTransport, servicenow_client_from_env
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

__all__ = [
    "IMPLEMENTATION_PACKET_TASK",
    "ActorType",
    "AllowlistPolicy",
    "ArtifactKind",
    "DataClassification",
    "DiscoveredField",
    "DiscoveredFormElement",
    "DiscoveredFormSection",
    "Document",
    "ExternalBuildPipelineResult",
    "ExternalBuildStatus",
    "InstanceDiscoveryContext",
    "LifecycleStateChangeEvent",
    "LifecycleWebhookBootstrapSpec",
    "PipelineInputs",
    "ProviderPolicy",
    "ProviderStatus",
    "RagDomain",
    "SpecializedRags",
    "StaticResponseProvider",
    "Story",
    "StoryType",
    "UpdateSetCandidate",
    "UpdateSetImporterBootstrapSpec",
    "UrllibTransport",
    "ValidationError",
    "WritebackClient",
    "WritebackExecutionRequest",
    "WritebackExecutionResult",
    "__version__",
    "apply_bootstrap_fields",
    "apply_bootstrap_fields_command",
    "apply_lifecycle_webhook_command",
    "apply_lifecycle_webhook_records",
    "apply_update_set_importer_command",
    "apply_update_set_importer_records",
    "attach_delivery_artifacts_command",
    "build_artifact_handoff_report",
    "build_artifact_handoff_work_note",
    "build_implementation_candidate_command",
    "build_implementation_packet",
    "build_implementation_packet_command",
    "build_lifecycle_webhook_bootstrap_spec",
    "build_reviewed_delivery_artifact_job",
    "build_update_set_importer_bootstrap_spec",
    "build_writeback_batch_report",
    "check_cicd_update_set_capability_command",
    "check_writeback_capability_command",
    "connect_operational_store",
    "delivery_attachment_jobs_from_report",
    "evaluate_cicd_update_set_capability",
    "evaluate_writeback_capability",
    "execute_writeback",
    "generate_implementation_update_set_candidate_from_packet",
    "lifecycle_webhook_servicenow_record_plan",
    "load_writeback_requests",
    "main",
    "init_operational_store_command",
    "plan_artifact_handoff_command",
    "plan_bootstrap_fields",
    "plan_bootstrap_fields_command",
    "plan_lifecycle_business_rule_command",
    "plan_story_ready_lifecycle_event",
    "plan_update_set_importer_command",
    "plan_writeback_command",
    "process_external_build_result_command",
    "process_lifecycle_event_command",
    "record_lifecycle_manifest_command",
    "review_delivery_artifact_command",
    "reviewed_delivery_jobs_from_build_result",
    "run_delivery_artifact_smoke_command",
    "run_implementation_candidates_command",
    "run_lifecycle_smoke_command",
    "run_local_command",
    "run_pdi_command",
    "run_pipeline",
    "run_reviewed_delivery_smoke_command",
    "run_writeback_batch",
    "run_writeback_batch_command",
    "servicenow_client_from_env",
    "update_set_importer_servicenow_record_plan",
    "verify_lifecycle_webhook_command",
    "verify_lifecycle_webhook_records",
    "verify_update_set_importer_command",
    "verify_update_set_importer_records",
    "verify_writeback",
    "verify_writeback_command",
    "write_artifact_handoff_summary_command",
    "write_candidate_artifact",
    "write_delivery_attachment_audit",
    "write_json_artifact_once",
    "write_lifecycle_manifest",
    "write_reviewed_delivery_lifecycle_manifest",
    "writeback_job_from_build_result",
]


def init_operational_store_command(args: argparse.Namespace) -> int:
    settings = load_runtime_settings(args.env_file)
    with connect_operational_store(settings.database_url) as store:
        if not store.verify_schema_ready():
            print("operational_store_schema_ready=false")
            return 1
    print("operational_store_schema_ready=true")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="jedi-devproject")
    parser.add_argument("--version", action="store_true", help="Print the project version.")
    subparsers = parser.add_subparsers(dest="command")
    run_local = subparsers.add_parser("run-local", help="Run the local candidate pipeline.")
    run_local.add_argument("--sample-file", type=Path, required=True)
    run_local.add_argument("--artifact-root", type=Path, default=Path("artifacts"))
    run_local.add_argument("--run-id", required=True)
    run_pdi = subparsers.add_parser("run-pdi", help="Run the pipeline from ServiceNow PDI.")
    run_pdi.add_argument("--env-file", type=Path, default=Path(".env"))
    run_pdi.add_argument("--artifact-root", type=Path, default=Path("artifacts"))
    run_pdi.add_argument("--run-id", required=True)
    run_pdi.add_argument("--limit", type=int, default=5)
    run_pdi.add_argument("--project-sys-id")
    run_pdi.add_argument("--sysparm-query")
    build_packet = subparsers.add_parser(
        "build-implementation-packet",
        help="Build reviewable LLM implementation packet artifacts from local stories.",
    )
    build_packet.add_argument("--sample-file", type=Path)
    build_packet.add_argument("--env-file", type=Path, default=Path(".env"))
    build_packet.add_argument("--story-number")
    build_packet.add_argument("--artifact-root", type=Path, default=Path("artifacts"))
    build_packet.add_argument("--run-id", required=True)
    build_candidate = subparsers.add_parser(
        "build-implementation-candidate",
        help=(
            "Build a validated implementation candidate artifact from an explicit "
            "provider response."
        ),
    )
    build_candidate.add_argument("--sample-file", type=Path)
    build_candidate.add_argument("--env-file", type=Path, default=Path(".env"))
    build_candidate.add_argument("--story-number")
    build_candidate.add_argument("--provider-response-file", type=Path, required=True)
    build_candidate.add_argument("--artifact-root", type=Path, default=Path("artifacts"))
    build_candidate.add_argument("--run-id", required=True)
    run_candidates = subparsers.add_parser(
        "run-implementation-candidates",
        help="Run implementation candidate jobs from a JSON file.",
    )
    run_candidates.add_argument("--jobs-file", type=Path, required=True)
    run_candidates.add_argument("--artifact-root", type=Path, default=Path("artifacts"))
    run_candidates.add_argument("--batch-report-root", type=Path, required=True)
    run_candidates.add_argument("--run-id", required=True)
    lifecycle_smoke = subparsers.add_parser(
        "run-lifecycle-smoke",
        help="Run a dry-run lifecycle smoke test from story fetch through writeback plan.",
    )
    lifecycle_smoke.add_argument("--env-file", type=Path, default=Path(".env"))
    lifecycle_smoke.add_argument("--story-number", required=True)
    lifecycle_smoke.add_argument("--provider-response-file", type=Path, required=True)
    lifecycle_smoke.add_argument("--artifact-root", type=Path, default=Path("artifacts"))
    lifecycle_smoke.add_argument("--run-id", required=True)
    lifecycle_smoke.add_argument("--build-reference", required=True)
    lifecycle_smoke.add_argument("--from-state", required=True)
    plan_writeback = subparsers.add_parser(
        "plan-writeback",
        help="Plan ServiceNow writeback for an external build result without applying it.",
    )
    plan_writeback.add_argument("--env-file", type=Path, default=Path(".env"))
    plan_writeback.add_argument("--story-number", required=True)
    plan_writeback.add_argument("--build-reference", required=True)
    plan_writeback.add_argument("--artifact-url")
    plan_writeback.add_argument(
        "--build-status",
        choices=[status.value for status in ExternalBuildStatus],
        default=ExternalBuildStatus.SUCCEEDED.value,
    )
    plan_writeback.add_argument("--from-state", required=True)
    plan_writeback.add_argument("--apply", action="store_true")
    plan_writeback.add_argument("--confirm-story-number")
    plan_writeback.add_argument(
        "--actor-type",
        choices=[actor_type.value for actor_type in ActorType],
        default=ActorType.SERVICE.value,
    )
    plan_writeback.add_argument("--actor-id")
    plan_writeback.add_argument("--execution-id")
    plan_writeback.add_argument("--audit-root", type=Path)
    plan_writeback.add_argument("--manifest-root", type=Path)
    plan_writeback.add_argument("--packet-path", type=Path)
    plan_writeback.add_argument("--candidate-path", type=Path)
    plan_writeback.add_argument("--candidate-batch-path", type=Path)
    check_writeback = subparsers.add_parser(
        "check-writeback-capability",
        help="Check whether the ServiceNow instance supports structured writeback.",
    )
    check_writeback.add_argument("--env-file", type=Path, default=Path(".env"))
    check_cicd_update_set = subparsers.add_parser(
        "check-cicd-update-set-capability",
        help="Check whether the ServiceNow instance exposes the CI/CD Update Set API.",
    )
    check_cicd_update_set.add_argument("--env-file", type=Path, default=Path(".env"))
    init_operational_store = subparsers.add_parser(
        "init-operational-store",
        help="Initialize and verify the PostgreSQL operational store schema.",
    )
    init_operational_store.add_argument("--env-file", type=Path, default=Path(".env"))
    verify_writeback_parser = subparsers.add_parser(
        "verify-writeback",
        help="Read ServiceNow and verify a completed structured writeback.",
    )
    verify_writeback_parser.add_argument("--env-file", type=Path, default=Path(".env"))
    verify_writeback_parser.add_argument("--story-number", required=True)
    verify_writeback_parser.add_argument("--build-reference", required=True)
    verify_writeback_parser.add_argument("--artifact-url")
    lifecycle_manifest = subparsers.add_parser(
        "record-lifecycle-manifest",
        help="Write a manifest tying lifecycle phase artifacts together.",
    )
    lifecycle_manifest.add_argument("--run-id", required=True)
    lifecycle_manifest.add_argument("--story-number", required=True)
    lifecycle_manifest.add_argument("--build-reference", required=True)
    lifecycle_manifest.add_argument("--packet-path", type=Path, required=True)
    lifecycle_manifest.add_argument("--candidate-path", type=Path, required=True)
    lifecycle_manifest.add_argument("--writeback-audit-path", type=Path)
    lifecycle_manifest.add_argument("--verification-verified", action="store_true")
    lifecycle_manifest.add_argument("--verification-state")
    lifecycle_manifest.add_argument("--manifest-root", type=Path, required=True)
    process_external_build = subparsers.add_parser(
        "process-external-build-result",
        help="Plan downstream jobs from an external build result contract.",
    )
    process_external_build.add_argument("--result-file", type=Path, required=True)
    process_external_build.add_argument("--from-state", required=True)
    process_external_build.add_argument("--run-id", required=True)
    process_external_build.add_argument("--writeback-job-root", type=Path, required=True)
    process_external_build.add_argument("--delivery-job-root", type=Path, required=True)
    process_lifecycle_event = subparsers.add_parser(
        "process-lifecycle-event",
        help="Plan local orchestration from a ServiceNow lifecycle event.",
    )
    process_lifecycle_event.add_argument("--event-file", type=Path, required=True)
    process_lifecycle_event.add_argument("--run-id", required=True)
    process_lifecycle_event.add_argument("--plan-root", type=Path, required=True)
    handoff = subparsers.add_parser(
        "plan-artifact-handoff",
        help="Write a report describing artifact attachment and link decisions.",
    )
    handoff.add_argument("--run-id", required=True)
    handoff.add_argument("--story-number", required=True)
    handoff.add_argument("--jobs-file", type=Path, required=True)
    handoff.add_argument("--report-root", type=Path, required=True)
    review_delivery = subparsers.add_parser(
        "review-delivery-artifact",
        help="Write a reviewed delivery artifact handoff job.",
    )
    review_delivery.add_argument("--run-id", required=True)
    review_delivery.add_argument("--story-number", required=True)
    review_delivery.add_argument(
        "--artifact-kind",
        choices=[ArtifactKind.UPDATE_SET_XML.value, ArtifactKind.TEST_EVIDENCE_BUNDLE.value],
        required=True,
    )
    review_delivery.add_argument("--artifact-path", type=Path, required=True)
    review_delivery.add_argument("--reviewer-id", required=True)
    review_delivery.add_argument("--job-root", type=Path, required=True)
    handoff_summary = subparsers.add_parser(
        "write-artifact-handoff-summary",
        help="Write a ServiceNow work note summarizing an artifact handoff report.",
    )
    handoff_summary.add_argument("--env-file", type=Path, default=Path(".env"))
    handoff_summary.add_argument("--report-file", type=Path, required=True)
    handoff_summary.add_argument("--apply", action="store_true")
    handoff_summary.add_argument("--confirm-story-number")
    handoff_summary.add_argument("--actor-id")
    attach_delivery = subparsers.add_parser(
        "attach-delivery-artifacts",
        help="Attach approved delivery artifacts from a handoff report.",
    )
    attach_delivery.add_argument("--env-file", type=Path, default=Path(".env"))
    attach_delivery.add_argument("--report-file", type=Path, required=True)
    attach_delivery.add_argument("--apply", action="store_true")
    attach_delivery.add_argument("--confirm-story-number")
    attach_delivery.add_argument("--actor-id")
    attach_delivery.add_argument("--audit-root", type=Path)
    attach_delivery.add_argument("--run-id")
    delivery_smoke = subparsers.add_parser(
        "run-delivery-artifact-smoke",
        help="Create a local placeholder delivery artifact and plan attachment.",
    )
    delivery_smoke.add_argument("--run-id", required=True)
    delivery_smoke.add_argument("--story-number", required=True)
    delivery_smoke.add_argument("--artifact-root", type=Path, default=Path("artifacts"))
    reviewed_delivery_smoke = subparsers.add_parser(
        "run-reviewed-delivery-smoke",
        help="Create a local reviewed delivery artifact and plan attachment.",
    )
    reviewed_delivery_smoke.add_argument("--run-id", required=True)
    reviewed_delivery_smoke.add_argument("--story-number", required=True)
    reviewed_delivery_smoke.add_argument("--reviewer-id", required=True)
    reviewed_delivery_smoke.add_argument(
        "--artifact-root",
        type=Path,
        default=Path("artifacts"),
    )
    plan_bootstrap = subparsers.add_parser(
        "plan-bootstrap-fields",
        help="Plan missing ServiceNow bootstrap table fields without applying changes.",
    )
    plan_bootstrap.add_argument("--env-file", type=Path, default=Path(".env"))
    apply_bootstrap = subparsers.add_parser(
        "apply-bootstrap-fields",
        help="Create missing ServiceNow bootstrap table fields with confirmation.",
    )
    apply_bootstrap.add_argument("--env-file", type=Path, default=Path(".env"))
    apply_bootstrap.add_argument("--confirm-table")
    apply_bootstrap.add_argument("--confirm-fields", action="store_true")
    apply_bootstrap.add_argument("--audit-root", type=Path, required=True)
    apply_bootstrap.add_argument("--run-id", default="bootstrap-fields")
    plan_lifecycle_business_rule = subparsers.add_parser(
        "plan-lifecycle-business-rule",
        help="Write a reviewable ServiceNow lifecycle Business Rule spec.",
    )
    plan_lifecycle_business_rule.add_argument("--endpoint-url", required=True)
    plan_lifecycle_business_rule.add_argument("--integration-identity", required=True)
    plan_lifecycle_business_rule.add_argument("--draft-state-value", required=True)
    plan_lifecycle_business_rule.add_argument("--ready-state-value", required=True)
    plan_lifecycle_business_rule.add_argument("--ready-for-testing-state-value")
    plan_lifecycle_business_rule.add_argument("--complete-state-value")
    plan_lifecycle_business_rule.add_argument("--hmac-secret-property-name")
    plan_lifecycle_business_rule.add_argument("--run-id", required=True)
    plan_lifecycle_business_rule.add_argument("--spec-root", type=Path, required=True)
    plan_update_set_importer = subparsers.add_parser(
        "plan-update-set-importer",
        help="Write a reviewable ServiceNow Update Set XML importer Scripted REST spec.",
    )
    plan_update_set_importer.add_argument("--integration-identity", required=True)
    plan_update_set_importer.add_argument("--run-id", required=True)
    plan_update_set_importer.add_argument("--spec-root", type=Path, required=True)
    apply_lifecycle_webhook = subparsers.add_parser(
        "apply-lifecycle-webhook",
        help="Create or update reviewed ServiceNow lifecycle webhook records.",
    )
    apply_lifecycle_webhook.add_argument("--env-file", type=Path, default=Path(".env"))
    apply_lifecycle_webhook.add_argument("--spec-file", type=Path, required=True)
    apply_lifecycle_webhook.add_argument("--confirm-table")
    apply_lifecycle_webhook.add_argument("--confirm-records", action="store_true")
    apply_lifecycle_webhook.add_argument("--audit-root", type=Path, required=True)
    apply_lifecycle_webhook.add_argument("--run-id", default="lifecycle-webhook")
    apply_update_set_importer = subparsers.add_parser(
        "apply-update-set-importer",
        help="Create or update reviewed ServiceNow Update Set XML importer records.",
    )
    apply_update_set_importer.add_argument("--env-file", type=Path, default=Path(".env"))
    apply_update_set_importer.add_argument("--spec-file", type=Path, required=True)
    apply_update_set_importer.add_argument("--confirm-service-id")
    apply_update_set_importer.add_argument("--confirm-records", action="store_true")
    apply_update_set_importer.add_argument("--audit-root", type=Path, required=True)
    apply_update_set_importer.add_argument("--run-id", default="update-set-importer")
    verify_lifecycle_webhook = subparsers.add_parser(
        "verify-lifecycle-webhook",
        help="Verify installed ServiceNow lifecycle webhook records.",
    )
    verify_lifecycle_webhook.add_argument("--env-file", type=Path, default=Path(".env"))
    verify_lifecycle_webhook.add_argument("--spec-file", type=Path, required=True)
    verify_lifecycle_webhook.add_argument("--report-root", type=Path, required=True)
    verify_lifecycle_webhook.add_argument("--run-id", required=True)
    verify_update_set_importer = subparsers.add_parser(
        "verify-update-set-importer",
        help="Verify installed ServiceNow Update Set XML importer records.",
    )
    verify_update_set_importer.add_argument("--env-file", type=Path, default=Path(".env"))
    verify_update_set_importer.add_argument("--spec-file", type=Path, required=True)
    verify_update_set_importer.add_argument("--report-root", type=Path, required=True)
    verify_update_set_importer.add_argument("--run-id", required=True)
    run_writeback = subparsers.add_parser(
        "run-writeback-batch",
        help="Run structured writeback jobs from a JSON file.",
    )
    run_writeback.add_argument("--env-file", type=Path, default=Path(".env"))
    run_writeback.add_argument("--jobs-file", type=Path, required=True)
    run_writeback.add_argument("--apply", action="store_true")
    run_writeback.add_argument(
        "--actor-type",
        choices=[actor_type.value for actor_type in ActorType],
        default=ActorType.SERVICE.value,
    )
    run_writeback.add_argument("--actor-id", required=True)
    run_writeback.add_argument("--execution-id")
    run_writeback.add_argument("--audit-root", type=Path, required=True)
    run_writeback.add_argument("--batch-report-root", type=Path, required=True)
    args = parser.parse_args(argv)

    if args.version:
        print(f"jedi-devproject-0 {__version__}")
        return 0

    if args.command == "run-local":
        return run_local_command(args)

    if args.command == "run-pdi":
        return run_pdi_command(args)

    if args.command == "build-implementation-packet":
        return build_implementation_packet_command(args, parser)

    if args.command == "build-implementation-candidate":
        return build_implementation_candidate_command(args, parser)

    if args.command == "run-implementation-candidates":
        return run_implementation_candidates_command(args)

    if args.command == "run-lifecycle-smoke":
        return run_lifecycle_smoke_command(args)

    if args.command == "plan-writeback":
        return plan_writeback_command(args, parser)

    if args.command == "check-writeback-capability":
        return check_writeback_capability_command(args)

    if args.command == "check-cicd-update-set-capability":
        return check_cicd_update_set_capability_command(args)

    if args.command == "init-operational-store":
        return init_operational_store_command(args)

    if args.command == "verify-writeback":
        return verify_writeback_command(args)

    if args.command == "record-lifecycle-manifest":
        return record_lifecycle_manifest_command(args)

    if args.command == "process-external-build-result":
        return process_external_build_result_command(args)

    if args.command == "process-lifecycle-event":
        return process_lifecycle_event_command(args)

    if args.command == "plan-artifact-handoff":
        return plan_artifact_handoff_command(args)

    if args.command == "review-delivery-artifact":
        return review_delivery_artifact_command(args)

    if args.command == "write-artifact-handoff-summary":
        return write_artifact_handoff_summary_command(args)

    if args.command == "attach-delivery-artifacts":
        return attach_delivery_artifacts_command(args)

    if args.command == "run-delivery-artifact-smoke":
        return run_delivery_artifact_smoke_command(args, parser)

    if args.command == "run-reviewed-delivery-smoke":
        return run_reviewed_delivery_smoke_command(args, parser)

    if args.command == "plan-bootstrap-fields":
        return plan_bootstrap_fields_command(args)

    if args.command == "apply-bootstrap-fields":
        return apply_bootstrap_fields_command(args)

    if args.command == "plan-lifecycle-business-rule":
        return plan_lifecycle_business_rule_command(args)

    if args.command == "plan-update-set-importer":
        return plan_update_set_importer_command(args)

    if args.command == "apply-lifecycle-webhook":
        return apply_lifecycle_webhook_command(args)

    if args.command == "apply-update-set-importer":
        return apply_update_set_importer_command(args)

    if args.command == "verify-lifecycle-webhook":
        return verify_lifecycle_webhook_command(args)

    if args.command == "verify-update-set-importer":
        return verify_update_set_importer_command(args)

    if args.command == "run-writeback-batch":
        return run_writeback_batch_command(args)

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
