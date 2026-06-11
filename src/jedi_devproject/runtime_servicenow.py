"""ServiceNow client wiring for the runtime: split PM/dev clients and story notifiers."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from jedi_devproject.fulfillment_worker import FulfillmentFailureNotifier
from jedi_devproject.lifecycle_api import LifecycleCompleteNotifier
from jedi_devproject.operational_store import FulfillmentJobRecord
from jedi_devproject.runtime_config import RuntimeSettings
from jedi_devproject.runtime_redaction import _redact_text
from jedi_devproject.servicenow import (
    HttpTransport,
    OAuthClientCredentials,
    ServiceNowClient,
    ServiceNowSettings,
)


def _servicenow_complete_notifier(*, client: ServiceNowClient) -> LifecycleCompleteNotifier:
    def notify(
        *,
        story_number: str,
        story_sys_id: str | None,
        event_id: str,
    ) -> None:
        if story_sys_id is None:
            raise RuntimeError(f"story_sys_id missing for completed story: {story_number}")
        client.update_story_fields(
            story_sys_id,
            {
                "u_ai_status": "Complete",
                "work_notes": (
                    "Automation loop closed after ServiceNow marked the story Complete. "
                    f"Lifecycle event: {event_id}."
                ),
            },
        )

    return notify


class SplitServiceNowClient:
    def __init__(
        self,
        *,
        story_client: ServiceNowClient,
        development_client: ServiceNowClient,
    ) -> None:
        self._story_client = story_client
        self._development_client = development_client

    def fetch_ready_stories(self, project_sys_id: str | None = None, *, limit: int = 100) -> Any:
        return self._story_client.fetch_ready_stories(project_sys_id=project_sys_id, limit=limit)

    def fetch_stories(self, sysparm_query: str | None = None, *, limit: int = 100) -> Any:
        return self._story_client.fetch_stories(sysparm_query=sysparm_query, limit=limit)

    def fetch_story_state_choices(self) -> Any:
        return self._story_client.fetch_story_state_choices()

    def fetch_story_dictionary_fields(self) -> Any:
        return self._story_client.fetch_story_dictionary_fields()

    def update_story_fields(self, story_sys_id: str, fields: dict[str, object]) -> Any:
        return self._story_client.update_story_fields(story_sys_id, fields)

    def fetch_table_record(self, *, table: str, lookup: dict[str, str]) -> Any:
        return self._development_client.fetch_table_record(table=table, lookup=lookup)

    def fetch_table_records(
        self,
        *,
        table: str,
        lookup: dict[str, str],
        fields: list[str] | None = None,
        limit: int = 100,
    ) -> Any:
        return self._development_client.fetch_table_records(
            table=table,
            lookup=lookup,
            fields=fields,
            limit=limit,
        )

    def upsert_table_record(
        self,
        *,
        table: str,
        lookup: dict[str, str],
        fields: dict[str, object],
    ) -> Any:
        return self._development_client.upsert_table_record(
            table=table,
            lookup=lookup,
            fields=fields,
        )

    def import_update_set_xml(self, *, service_id: str, update_set_xml: str) -> Any:
        return self._development_client.import_update_set_xml(
            service_id=service_id,
            update_set_xml=update_set_xml,
        )


def _servicenow_story_client_from_settings(
    *,
    settings: RuntimeSettings,
    transport: HttpTransport,
) -> ServiceNowClient:
    return _servicenow_client(
        instance_url=settings.servicenow_pm_instance_url or settings.servicenow_instance_url,
        client_id=settings.servicenow_pm_client_id or settings.servicenow_client_id,
        client_secret=settings.servicenow_pm_client_secret or settings.servicenow_client_secret,
        transport=transport,
    )


def _servicenow_development_client_from_settings(
    *,
    settings: RuntimeSettings,
    transport: HttpTransport,
) -> ServiceNowClient:
    return _servicenow_client(
        instance_url=settings.servicenow_dev_instance_url or settings.servicenow_instance_url,
        client_id=settings.servicenow_dev_client_id or settings.servicenow_client_id,
        client_secret=settings.servicenow_dev_client_secret or settings.servicenow_client_secret,
        transport=transport,
    )


def _servicenow_pm_and_dev_settings_match(settings: RuntimeSettings) -> bool:
    return (
        (settings.servicenow_pm_instance_url or settings.servicenow_instance_url)
        == (settings.servicenow_dev_instance_url or settings.servicenow_instance_url)
        and (settings.servicenow_pm_client_id or settings.servicenow_client_id)
        == (settings.servicenow_dev_client_id or settings.servicenow_client_id)
        and (settings.servicenow_pm_client_secret or settings.servicenow_client_secret)
        == (settings.servicenow_dev_client_secret or settings.servicenow_client_secret)
    )


def _servicenow_client(
    *,
    instance_url: str,
    client_id: str,
    client_secret: str,
    transport: HttpTransport,
) -> ServiceNowClient:
    auth = OAuthClientCredentials(
        instance_url=instance_url,
        client_id=client_id,
        client_secret=client_secret,
        transport=transport,
    )
    return ServiceNowClient(
        settings=ServiceNowSettings(instance_url=instance_url),
        auth=auth,
        transport=transport,
    )


def _servicenow_failure_notifier(
    *,
    client: ServiceNowClient,
    secret_values: Iterable[str] = (),
) -> FulfillmentFailureNotifier:
    def notify(job: FulfillmentJobRecord, error_message: str) -> None:
        fulfillment_job = FulfillmentJobRecord.model_validate(job)
        stories = client.fetch_stories(
            sysparm_query=(
                f"sys_id={fulfillment_job.story_sys_id}"
                if fulfillment_job.story_sys_id
                else f"number={fulfillment_job.story_number}"
            ),
            limit=1,
        )
        if not stories:
            raise RuntimeError(f"story not found: {fulfillment_job.story_number}")
        fields: dict[str, object] = {
            "u_ai_status": "Automation Failed",
            "work_notes": (
                "Automated fulfillment failed for lifecycle event "
                f"{fulfillment_job.event_id}. Job: {fulfillment_job.job_id}. "
                f"Error: {_redact_text(error_message, secret_values)}"
            ),
        }
        draft_state = _story_state_choice_value(client=client, label="Draft")
        if draft_state is not None:
            fields["state"] = draft_state
        client.update_story_fields(
            stories[0].sys_id,
            fields,
        )

    return notify


def _story_state_choice_value(*, client: ServiceNowClient, label: str) -> str | None:
    normalized_label = label.strip().lower()
    for choice in client.fetch_story_state_choices():
        if choice.label.strip().lower() == normalized_label:
            return choice.value
    return None
