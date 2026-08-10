"""ServiceNow client wiring for the runtime: split PM/dev clients and story notifiers."""

from __future__ import annotations

import re
from collections.abc import Iterable
from typing import Any, cast

from jedi_devproject.fulfillment_worker import FulfillmentFailureNotifier
from jedi_devproject.lifecycle_api import LifecycleCompleteNotifier
from jedi_devproject.literal_secret_values import safe_literal_secret_values
from jedi_devproject.models import Story
from jedi_devproject.operational_store import FulfillmentJobRecord
from jedi_devproject.runtime_config import (
    RuntimeConfigError,
    RuntimeSettings,
    _runtime_setting_text,
    _servicenow_instance_url_value_errors,
    _servicenow_oauth_value_errors,
)
from jedi_devproject.runtime_redaction import _redact_text
from jedi_devproject.servicenow import (
    HttpTransport,
    OAuthClientCredentials,
    ServiceNowClient,
    ServiceNowSettings,
    StoryStateChoice,
)
from jedi_devproject.work_note_safety import safe_work_note_value

MAX_FAILURE_NOTIFIER_STORY_LOOKUP_PART_CHARS = 1024
MAX_FAILURE_NOTIFIER_STATE_CHOICE_TEXT_CHARS = 1024
STORY_LOOKUP_QUERY_UNSAFE_DIAGNOSTIC = "story lookup query is unsafe"
STORY_LOOKUP_RESULT_UNSAFE_DIAGNOSTIC = "story lookup result is unsafe"
STORY_STATE_CHOICES_RESULT_UNSAFE_DIAGNOSTIC = "story state choices result is unsafe"
STORY_DICTIONARY_FIELDS_RESULT_UNSAFE_DIAGNOSTIC = (
    "story dictionary fields result is unsafe"
)
STORY_MUTATION_RESULT_UNSAFE_DIAGNOSTIC = "story mutation result is unsafe"
TABLE_RECORD_LOOKUP_RESULT_UNSAFE_DIAGNOSTIC = "table record lookup result is unsafe"
TABLE_MUTATION_RESULT_UNSAFE_DIAGNOSTIC = "table mutation result is unsafe"
UPDATE_SET_IMPORT_RESULT_UNSAFE_DIAGNOSTIC = "update set import result is unsafe"
COMPLETE_STORY_SYS_ID_UNSAFE_DIAGNOSTIC = "completed story_sys_id is unsafe"
_FAILURE_NOTIFIER_RECORD_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]+$")


def _servicenow_complete_notifier(*, client: ServiceNowClient) -> LifecycleCompleteNotifier:
    def notify(
        *,
        story_number: str,
        story_sys_id: str | None,
        event_id: str,
    ) -> None:
        if story_sys_id is None:
            safe_story_number = safe_work_note_value(story_number)
            raise RuntimeError(
                f"story_sys_id missing for completed story: {safe_story_number}"
            )
        safe_story_sys_id = _safe_completion_story_sys_id(story_sys_id)
        safe_event_id = safe_work_note_value(event_id)
        client.update_story_fields(
            safe_story_sys_id,
            {
                "u_ai_status": "Complete",
                "work_notes": (
                    "Automation loop closed after ServiceNow marked the story Complete. "
                    f"Lifecycle event: {safe_event_id}."
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
        return _split_story_lookup_results(
            self._story_client.fetch_ready_stories(
                project_sys_id=project_sys_id,
                limit=limit,
            )
        )

    def fetch_stories(self, sysparm_query: str | None = None, *, limit: int = 100) -> Any:
        return _split_story_lookup_results(
            self._story_client.fetch_stories(sysparm_query=sysparm_query, limit=limit)
        )

    def fetch_story_state_choices(self) -> Any:
        return _split_story_state_choice_results(
            self._story_client.fetch_story_state_choices()
        )

    def fetch_story_dictionary_fields(self) -> Any:
        return _split_story_dictionary_field_results(
            self._story_client.fetch_story_dictionary_fields()
        )

    def update_story_fields(self, story_sys_id: str, fields: dict[str, object]) -> Any:
        return _split_story_mutation_result(
            self._story_client.update_story_fields(story_sys_id, fields)
        )

    def fetch_table_record(self, *, table: str, lookup: dict[str, str]) -> Any:
        return _split_optional_table_record_result(
            self._development_client.fetch_table_record(table=table, lookup=lookup)
        )

    def fetch_table_records(
        self,
        *,
        table: str,
        lookup: dict[str, str],
        fields: list[str] | None = None,
        limit: int = 100,
    ) -> Any:
        return _split_table_record_lookup_results(
            self._development_client.fetch_table_records(
                table=table,
                lookup=lookup,
                fields=fields,
                limit=limit,
            )
        )

    def upsert_table_record(
        self,
        *,
        table: str,
        lookup: dict[str, str],
        fields: dict[str, object],
    ) -> Any:
        return _split_table_mutation_result(
            self._development_client.upsert_table_record(
                table=table,
                lookup=lookup,
                fields=fields,
            )
        )

    def import_update_set_xml(self, *, service_id: str, update_set_xml: str) -> Any:
        return _split_update_set_import_result(
            self._development_client.import_update_set_xml(
                service_id=service_id,
                update_set_xml=update_set_xml,
            )
        )


def _split_story_lookup_results(stories: object) -> list[Any]:
    if type(stories) is not list:
        raise RuntimeError(STORY_LOOKUP_RESULT_UNSAFE_DIAGNOSTIC)
    return stories


def _split_story_mutation_result(result: object) -> dict[str, Any]:
    if type(result) is not dict:
        raise RuntimeError(STORY_MUTATION_RESULT_UNSAFE_DIAGNOSTIC)
    return result


def _split_table_record_lookup_results(records: object) -> list[Any]:
    if type(records) is not list:
        raise RuntimeError(TABLE_RECORD_LOOKUP_RESULT_UNSAFE_DIAGNOSTIC)
    return records


def _split_optional_table_record_result(record: object) -> dict[str, Any] | None:
    if record is None:
        return None
    if type(record) is not dict:
        raise RuntimeError(TABLE_RECORD_LOOKUP_RESULT_UNSAFE_DIAGNOSTIC)
    return record


def _split_table_mutation_result(result: object) -> dict[str, Any]:
    if type(result) is not dict:
        raise RuntimeError(TABLE_MUTATION_RESULT_UNSAFE_DIAGNOSTIC)
    return result


def _split_update_set_import_result(result: object) -> dict[str, Any]:
    if type(result) is not dict:
        raise RuntimeError(UPDATE_SET_IMPORT_RESULT_UNSAFE_DIAGNOSTIC)
    return result


def _split_story_state_choice_results(choices: object) -> list[Any]:
    if type(choices) is not list:
        raise RuntimeError(STORY_STATE_CHOICES_RESULT_UNSAFE_DIAGNOSTIC)
    return choices


def _split_story_dictionary_field_results(fields: object) -> list[Any]:
    if type(fields) is not list:
        raise RuntimeError(STORY_DICTIONARY_FIELDS_RESULT_UNSAFE_DIAGNOSTIC)
    return fields


def _servicenow_story_client_from_settings(
    *,
    settings: RuntimeSettings,
    transport: HttpTransport,
) -> ServiceNowClient:
    connection_settings = _servicenow_runtime_connection_settings(settings)
    return _servicenow_client(
        instance_url=connection_settings.pm_instance_url,
        client_id=connection_settings.pm_client_id,
        client_secret=connection_settings.pm_client_secret,
        transport=transport,
    )


def _servicenow_development_client_from_settings(
    *,
    settings: RuntimeSettings,
    transport: HttpTransport,
) -> ServiceNowClient:
    connection_settings = _servicenow_runtime_connection_settings(settings)
    return _servicenow_client(
        instance_url=connection_settings.dev_instance_url,
        client_id=connection_settings.dev_client_id,
        client_secret=connection_settings.dev_client_secret,
        transport=transport,
    )


def _servicenow_pm_and_dev_settings_match(settings: RuntimeSettings) -> bool:
    connection_settings = _servicenow_runtime_connection_settings(settings)
    return (
        connection_settings.pm_instance_url == connection_settings.dev_instance_url
        and connection_settings.pm_client_id == connection_settings.dev_client_id
        and connection_settings.pm_client_secret == connection_settings.dev_client_secret
    )


class _ServiceNowRuntimeConnectionSettings:
    def __init__(
        self,
        *,
        pm_instance_url: str,
        pm_client_id: str,
        pm_client_secret: str,
        dev_instance_url: str,
        dev_client_id: str,
        dev_client_secret: str,
    ) -> None:
        self.pm_instance_url = pm_instance_url
        self.pm_client_id = pm_client_id
        self.pm_client_secret = pm_client_secret
        self.dev_instance_url = dev_instance_url
        self.dev_client_id = dev_client_id
        self.dev_client_secret = dev_client_secret


def _servicenow_runtime_connection_settings(
    settings: RuntimeSettings,
) -> _ServiceNowRuntimeConnectionSettings:
    base_instance_url = _runtime_setting_text(
        settings.servicenow_instance_url,
        name="SERVICENOW_INSTANCE_URL",
    )
    base_client_id = _runtime_setting_text(
        settings.servicenow_client_id,
        name="SERVICENOW_CLIENT_ID",
    )
    base_client_secret = _runtime_setting_text(
        settings.servicenow_client_secret,
        name="SERVICENOW_CLIENT_SECRET",
    )
    pm_instance_override = _runtime_setting_text(
        settings.servicenow_pm_instance_url,
        name="SERVICENOW_PM_INSTANCE_URL",
    )
    pm_client_id_override = _runtime_setting_text(
        settings.servicenow_pm_client_id,
        name="SERVICENOW_PM_CLIENT_ID",
    )
    pm_client_secret_override = _runtime_setting_text(
        settings.servicenow_pm_client_secret,
        name="SERVICENOW_PM_CLIENT_SECRET",
    )
    dev_instance_override = _runtime_setting_text(
        settings.servicenow_dev_instance_url,
        name="SERVICENOW_DEV_INSTANCE_URL",
    )
    dev_client_id_override = _runtime_setting_text(
        settings.servicenow_dev_client_id,
        name="SERVICENOW_DEV_CLIENT_ID",
    )
    dev_client_secret_override = _runtime_setting_text(
        settings.servicenow_dev_client_secret,
        name="SERVICENOW_DEV_CLIENT_SECRET",
    )
    _raise_servicenow_runtime_connection_errors(
        {
            "SERVICENOW_INSTANCE_URL": base_instance_url,
            "SERVICENOW_PM_INSTANCE_URL": pm_instance_override,
            "SERVICENOW_DEV_INSTANCE_URL": dev_instance_override,
        },
        {
            "SERVICENOW_CLIENT_ID": base_client_id,
            "SERVICENOW_CLIENT_SECRET": base_client_secret,
            "SERVICENOW_PM_CLIENT_ID": pm_client_id_override,
            "SERVICENOW_PM_CLIENT_SECRET": pm_client_secret_override,
            "SERVICENOW_DEV_CLIENT_ID": dev_client_id_override,
            "SERVICENOW_DEV_CLIENT_SECRET": dev_client_secret_override,
        },
    )
    pm_client_secret = pm_client_secret_override
    # Empty string is an invalid override sentinel, not a hardcoded secret.
    if pm_client_secret == "":  # nosec B105
        pm_client_secret = base_client_secret
    dev_client_secret = dev_client_secret_override
    # Empty string is an invalid override sentinel, not a hardcoded secret.
    if dev_client_secret == "":  # nosec B105
        dev_client_secret = base_client_secret
    return _ServiceNowRuntimeConnectionSettings(
        pm_instance_url=pm_instance_override if pm_instance_override != "" else base_instance_url,
        pm_client_id=pm_client_id_override if pm_client_id_override != "" else base_client_id,
        pm_client_secret=pm_client_secret,
        dev_instance_url=dev_instance_override
        if dev_instance_override != ""
        else base_instance_url,
        dev_client_id=dev_client_id_override if dev_client_id_override != "" else base_client_id,
        dev_client_secret=dev_client_secret,
    )


def _raise_servicenow_runtime_connection_errors(
    instance_values_by_name: dict[str, str],
    credential_values_by_name: dict[str, str],
) -> None:
    errors = [
        *_servicenow_instance_url_value_errors(
            values_by_name=instance_values_by_name,
            detail="for runtime ServiceNow client construction",
        ),
        *_servicenow_oauth_value_errors(
            values_by_name=credential_values_by_name,
            detail="for runtime ServiceNow client construction",
        ),
    ]
    if errors:
        raise RuntimeConfigError("; ".join(errors))


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
    secret_values_tuple = safe_literal_secret_values(secret_values)

    def notify(job: FulfillmentJobRecord, error_message: str) -> None:
        fulfillment_job = FulfillmentJobRecord.model_validate(job)
        stories = _failure_notifier_stories(
            client.fetch_stories(
                sysparm_query=_failure_notifier_story_lookup_query(fulfillment_job),
                limit=1,
            )
        )
        if not stories:
            safe_story_number = safe_work_note_value(
                fulfillment_job.story_number,
                secret_values=secret_values_tuple,
            )
            raise RuntimeError(f"story not found: {safe_story_number}")
        safe_event_id = safe_work_note_value(
            fulfillment_job.event_id,
            secret_values=secret_values_tuple,
        )
        safe_job_id = safe_work_note_value(
            fulfillment_job.job_id,
            secret_values=secret_values_tuple,
        )
        safe_error_message = safe_work_note_value(
            _redact_text(error_message, secret_values_tuple),
            secret_values=secret_values_tuple,
        )
        fields: dict[str, object] = {
            "u_ai_status": "Automation Failed",
            "work_notes": (
                "Automated fulfillment failed for lifecycle event "
                f"{safe_event_id}. Job: {safe_job_id}. "
                f"Error: {safe_error_message}"
            ),
        }
        draft_state = _story_state_choice_value(client=client, label="Draft")
        if draft_state is not None:
            fields["state"] = draft_state
        story_sys_id = _safe_failure_notifier_found_story_sys_id(stories[0])
        client.update_story_fields(story_sys_id, fields)

    return notify


def _failure_notifier_stories(stories: object) -> list[object]:
    if type(stories) is not list:
        raise RuntimeError(STORY_LOOKUP_RESULT_UNSAFE_DIAGNOSTIC)
    return cast(list[object], stories)


def _failure_notifier_story_lookup_query(job: FulfillmentJobRecord) -> str:
    if job.story_sys_id:
        return f"sys_id={_safe_failure_notifier_story_sys_id(job.story_sys_id)}"
    return f"number={_safe_failure_notifier_story_lookup_part(job.story_number)}"


def _safe_failure_notifier_story_sys_id(value: object) -> str:
    if not _valid_failure_notifier_record_id(value):
        raise RuntimeError(STORY_LOOKUP_QUERY_UNSAFE_DIAGNOSTIC)
    return cast(str, value)


def _safe_completion_story_sys_id(value: object) -> str:
    if not _valid_failure_notifier_record_id(value):
        raise RuntimeError(COMPLETE_STORY_SYS_ID_UNSAFE_DIAGNOSTIC)
    return cast(str, value)


def _safe_failure_notifier_found_story_sys_id(story: object) -> str:
    value: object
    if isinstance(story, Story):
        value = story.sys_id
    elif type(story) is dict:
        value = story.get("sys_id")
    else:
        raise RuntimeError(STORY_LOOKUP_RESULT_UNSAFE_DIAGNOSTIC)
    if not _valid_failure_notifier_record_id(value):
        raise RuntimeError(STORY_LOOKUP_RESULT_UNSAFE_DIAGNOSTIC)
    return cast(str, value)


def _valid_failure_notifier_record_id(value: object) -> bool:
    return (
        type(value) is str
        and value.strip() == value
        and len(value) <= MAX_FAILURE_NOTIFIER_STORY_LOOKUP_PART_CHARS
        and bool(_FAILURE_NOTIFIER_RECORD_ID_PATTERN.fullmatch(value))
    )


def _safe_failure_notifier_story_lookup_part(value: object) -> str:
    if (
        type(value) is not str
        or value == ""
        or len(value) > MAX_FAILURE_NOTIFIER_STORY_LOOKUP_PART_CHARS
        or "^" in value
        or "=" in value
        or any(ord(character) < 32 for character in value)
    ):
        raise RuntimeError(STORY_LOOKUP_QUERY_UNSAFE_DIAGNOSTIC)
    return value


def _story_state_choice_value(*, client: ServiceNowClient, label: str) -> str | None:
    normalized_label = label.strip().lower()
    for choice in client.fetch_story_state_choices():
        choice_label: object
        choice_value: object
        if isinstance(choice, StoryStateChoice):
            choice_label = choice.label
            choice_value = choice.value
        elif type(choice) is dict:
            choice_label = choice.get("label")
            choice_value = choice.get("value")
        else:
            continue
        if not _safe_state_choice_text(choice_label) or not _safe_state_choice_text(choice_value):
            continue
        if choice_label.strip().lower() == normalized_label:
            return choice_value
    return None


def _safe_state_choice_text(value: object) -> bool:
    return (
        type(value) is str
        and value.strip() == value
        and len(value) <= MAX_FAILURE_NOTIFIER_STATE_CHOICE_TEXT_CHARS
        and not any(ord(character) < 32 for character in value)
    )
