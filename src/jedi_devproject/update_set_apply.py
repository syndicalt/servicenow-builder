from __future__ import annotations

from typing import Any, Protocol

from pydantic import BaseModel, ConfigDict

from jedi_devproject.models import CandidateChange, CandidateStatus, UpdateSetCandidate


class UpdateSetApplyClient(Protocol):
    def fetch_table_record(
        self,
        *,
        table: str,
        lookup: dict[str, str],
    ) -> dict[str, Any] | None: ...

    def fetch_table_records(
        self,
        *,
        table: str,
        lookup: dict[str, str],
        fields: list[str] | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]: ...

    def upsert_table_record(
        self,
        *,
        table: str,
        lookup: dict[str, str],
        fields: dict[str, Any],
    ) -> dict[str, Any]: ...


class UpdateSetApplyRequest(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, extra="forbid")

    update_set_sys_id: str
    integration_user_name: str
    candidate: UpdateSetCandidate


class UpdateSetApplyResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    applied_change_count: int
    customer_update_count: int


def apply_candidate_to_update_set(
    *,
    client: UpdateSetApplyClient,
    request: UpdateSetApplyRequest,
) -> UpdateSetApplyResult:
    if request.candidate.status is not CandidateStatus.READY_FOR_REVIEW:
        raise ValueError("candidate is not ready for Update Set apply")
    normalized_changes = [
        _normalize_supported_change(change) for change in request.candidate.changes
    ]

    user_sys_id = _integration_user_sys_id(
        client=client,
        integration_user_name=request.integration_user_name,
    )
    _set_current_update_set(
        client=client,
        user_sys_id=user_sys_id,
        update_set_sys_id=request.update_set_sys_id,
    )
    for change in normalized_changes:
        _apply_dictionary_change(client=client, change=change)

    customer_updates = client.fetch_table_records(
        table="sys_update_xml",
        lookup={"update_set": request.update_set_sys_id},
        fields=["sys_id", "name", "target_name", "type"],
        limit=100,
    )
    if not customer_updates:
        raise RuntimeError(
            f"no customer updates captured for generated Update Set {request.update_set_sys_id}"
        )
    return UpdateSetApplyResult(
        applied_change_count=len(normalized_changes),
        customer_update_count=len(customer_updates),
    )


def _normalize_supported_change(change: CandidateChange) -> CandidateChange:
    if change.table != "sys_dictionary":
        raise ValueError(f"unsupported update-set apply table: {change.table}")
    if change.operation not in {"insert", "update"}:
        raise ValueError(f"unsupported update-set apply operation: {change.operation}")
    fields = dict(change.fields)
    if "element" not in fields and "column_name" in fields:
        fields["element"] = fields.pop("column_name")

    required_fields = ["name", "element", "column_label", "internal_type"]
    missing = [
        field_name
        for field_name in required_fields
        if str(fields.get(field_name) or "").strip() == ""
    ]
    if missing:
        raise ValueError(
            "sys_dictionary change missing required fields: " + ", ".join(missing)
        )
    return change.model_copy(update={"fields": _service_now_field_values(fields)})


def _service_now_field_values(fields: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(fields)
    if "max_length" in normalized and normalized["max_length"] is not None:
        normalized["max_length"] = str(normalized["max_length"])
    return normalized


def _integration_user_sys_id(
    *,
    client: UpdateSetApplyClient,
    integration_user_name: str,
) -> str:
    user_record = client.fetch_table_record(
        table="sys_user",
        lookup={"user_name": integration_user_name},
    )
    user_sys_id = "" if user_record is None else str(user_record.get("sys_id", ""))
    if user_sys_id.strip() == "":
        raise RuntimeError(f"integration user not found: {integration_user_name}")
    return user_sys_id


def _set_current_update_set(
    *,
    client: UpdateSetApplyClient,
    user_sys_id: str,
    update_set_sys_id: str,
) -> None:
    client.upsert_table_record(
        table="sys_user_preference",
        lookup={"name": "sys_update_set", "user": user_sys_id},
        fields={
            "name": "sys_update_set",
            "user": user_sys_id,
            "value": update_set_sys_id,
        },
    )


def _apply_dictionary_change(
    *,
    client: UpdateSetApplyClient,
    change: CandidateChange,
) -> None:
    client.upsert_table_record(
        table="sys_dictionary",
        lookup={
            "name": str(change.fields["name"]),
            "element": str(change.fields["element"]),
        },
        fields=change.fields,
    )
