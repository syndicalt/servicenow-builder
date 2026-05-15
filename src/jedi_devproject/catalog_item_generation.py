from __future__ import annotations

import hashlib
import re
from html import escape
from typing import Any, Protocol

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from jedi_devproject.models import CandidateChange


class CatalogMetadataClient(Protocol):
    def fetch_table_records(
        self,
        *,
        table: str,
        lookup: dict[str, str],
        fields: list[str] | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]: ...


class CatalogResolvedReference(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sys_id: str
    display: str


class CatalogVariableIntent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    label: str
    variable_type: str
    order: int = 100
    mandatory: bool = False
    reference_table: str | None = None
    reference_qualifier: str | None = None
    default_value: str = ""
    help_text: str = ""

    @field_validator("name", "label", "variable_type")
    @classmethod
    def require_text(cls, value: str) -> str:
        cleaned = value.strip()
        if cleaned == "":
            raise ValueError("must not be empty")
        return cleaned

    @model_validator(mode="after")
    def require_supported_type(self) -> CatalogVariableIntent:
        if self.variable_type not in CATALOG_VARIABLE_TYPE_IDS:
            raise ValueError(f"unsupported catalog variable type: {self.variable_type}")
        if self.variable_type == "reference" and not (self.reference_table or "").strip():
            raise ValueError("reference catalog variables require reference_table")
        return self


class CatalogItemIntent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    short_description: str
    description: str = ""
    catalog: str
    category: str
    taxonomy: str
    employee_center_topic: str
    variables: list[CatalogVariableIntent]

    @field_validator(
        "name",
        "short_description",
        "catalog",
        "category",
        "taxonomy",
        "employee_center_topic",
    )
    @classmethod
    def require_text(cls, value: str) -> str:
        cleaned = value.strip()
        if cleaned == "":
            raise ValueError("must not be empty")
        return cleaned

    @model_validator(mode="after")
    def require_variables(self) -> CatalogItemIntent:
        if not self.variables:
            raise ValueError("catalog item requires at least one variable")
        names = [variable.name for variable in self.variables]
        if len(set(names)) != len(names):
            raise ValueError("catalog variable names must be unique")
        return self


class CatalogResolvedContext(BaseModel):
    model_config = ConfigDict(extra="forbid")

    catalog: CatalogResolvedReference
    category: CatalogResolvedReference
    taxonomy: CatalogResolvedReference
    topic: CatalogResolvedReference
    content_type: CatalogResolvedReference


CATALOG_VARIABLE_TYPE_IDS = {
    "yes_no": "1",
    "multi_line_text": "2",
    "checkbox": "7",
    "reference": "8",
    "date": "9",
    "single_line_text": "6",
}


def catalog_item_customer_updates(
    *,
    client: CatalogMetadataClient,
    changes: list[CandidateChange],
    remote_update_set_sys_id: str,
) -> list[dict[str, Any]]:
    intent = _catalog_item_intent(changes)
    context = _resolve_catalog_context(client=client, intent=intent)
    catalog_item_sys_id = _stable_sys_id("sc_cat_item", intent.name)
    variable_sys_ids = {
        variable.name: _stable_sys_id("item_option_new", intent.name, variable.name)
        for variable in intent.variables
    }
    return [
        _catalog_item_update(
            intent=intent,
            context=context,
            catalog_item_sys_id=catalog_item_sys_id,
            remote_update_set_sys_id=remote_update_set_sys_id,
        ),
        *[
            _catalog_variable_update(
                intent=intent,
                variable=variable,
                variable_sys_id=variable_sys_ids[variable.name],
                catalog_item_sys_id=catalog_item_sys_id,
                remote_update_set_sys_id=remote_update_set_sys_id,
            )
            for variable in intent.variables
        ],
        _catalog_category_update(
            intent=intent,
            context=context,
            catalog_item_sys_id=catalog_item_sys_id,
            remote_update_set_sys_id=remote_update_set_sys_id,
        ),
        _connected_content_update(
            intent=intent,
            context=context,
            catalog_item_sys_id=catalog_item_sys_id,
            remote_update_set_sys_id=remote_update_set_sys_id,
        ),
    ]


def _catalog_item_intent(changes: list[CandidateChange]) -> CatalogItemIntent:
    catalog_change = next((change for change in changes if change.table == "sc_cat_item"), None)
    if catalog_change is None:
        raise ValueError("Catalog Item handoff requires one sc_cat_item change")
    if catalog_change.operation != "insert":
        raise ValueError("Catalog Item handoff supports insert only")
    item_fields = dict(catalog_change.fields)
    variables = [
        _catalog_variable_intent(change)
        for change in changes
        if change.table == "item_option_new"
    ]
    category_fields = _first_change_fields(changes, "sc_cat_item_category")
    topic_fields = _first_change_fields(changes, "m2m_connected_content")
    return CatalogItemIntent(
        name=str(item_fields.get("name") or item_fields.get("artifact_name") or ""),
        short_description=str(item_fields.get("short_description") or ""),
        description=str(item_fields.get("description") or ""),
        catalog=str(item_fields.get("catalog") or category_fields.get("catalog") or ""),
        category=str(item_fields.get("category") or category_fields.get("category") or ""),
        taxonomy=str(item_fields.get("taxonomy") or topic_fields.get("taxonomy") or ""),
        employee_center_topic=str(
            item_fields.get("employee_center_topic")
            or item_fields.get("topic")
            or topic_fields.get("topic")
            or topic_fields.get("employee_center_topic")
            or ""
        ),
        variables=variables,
    )


def _catalog_variable_intent(change: CandidateChange) -> CatalogVariableIntent:
    if change.operation != "insert":
        raise ValueError("Catalog Item variable handoff supports insert only")
    fields = dict(change.fields)
    variable_type = _normalize_variable_type(str(fields.get("type") or ""))
    return CatalogVariableIntent(
        name=_normalize_name(str(fields.get("name") or fields.get("variable_name") or "")),
        label=str(fields.get("question_text") or fields.get("label") or ""),
        variable_type=variable_type,
        order=_optional_int(fields.get("order")) or 100,
        mandatory=_bool_value(fields.get("mandatory")),
        reference_table=str(fields.get("reference") or fields.get("reference_table") or ""),
        reference_qualifier=str(
            fields.get("reference_qualifier")
            or fields.get("reference_qual")
            or fields.get("reference_qual_condition")
            or ""
        ),
        default_value=str(fields.get("default_value") or ""),
        help_text=str(fields.get("help_text") or ""),
    )


def _resolve_catalog_context(
    *,
    client: CatalogMetadataClient,
    intent: CatalogItemIntent,
) -> CatalogResolvedContext:
    catalogs = client.fetch_table_records(
        table="sc_catalog",
        lookup={},
        fields=["sys_id", "title", "active"],
        limit=100,
    )
    catalog = _resolve_named_record(
        records=catalogs,
        display_name=intent.catalog,
        label="catalog",
        name_fields=("title", "name"),
    )
    categories = client.fetch_table_records(
        table="sc_category",
        lookup={},
        fields=["sys_id", "title", "active", "sc_catalog"],
        limit=250,
    )
    category = _resolve_category(
        records=categories,
        display_name=intent.category,
        catalog_sys_id=catalog.sys_id,
    )
    taxonomies = client.fetch_table_records(
        table="taxonomy",
        lookup={},
        fields=["sys_id", "name", "active"],
        limit=100,
    )
    taxonomy = _resolve_named_record(
        records=taxonomies,
        display_name=intent.taxonomy,
        label="taxonomy",
        name_fields=("name",),
    )
    topics = client.fetch_table_records(
        table="topic",
        lookup={},
        fields=["sys_id", "name", "topic_path", "active", "taxonomy"],
        limit=250,
    )
    topic = _resolve_topic(
        records=topics,
        display_name=intent.employee_center_topic,
        taxonomy_sys_id=taxonomy.sys_id,
    )
    content_types = client.fetch_table_records(
        table="taxonomy_content_configuration",
        lookup={},
        fields=["sys_id", "name", "active"],
        limit=100,
    )
    content_type = _resolve_named_record(
        records=content_types,
        display_name="Catalog Item",
        label="Catalog Item content type",
        name_fields=("name",),
    )
    return CatalogResolvedContext(
        catalog=catalog,
        category=category,
        taxonomy=taxonomy,
        topic=topic,
        content_type=content_type,
    )


def _catalog_item_update(
    *,
    intent: CatalogItemIntent,
    context: CatalogResolvedContext,
    catalog_item_sys_id: str,
    remote_update_set_sys_id: str,
) -> dict[str, Any]:
    update_name = f"sc_cat_item_{catalog_item_sys_id}"
    return {
        "name": update_name,
        "remote_update_set": remote_update_set_sys_id,
        "action": "INSERT_OR_UPDATE",
        "type": "Catalog Item",
        "target_name": intent.name,
        "payload": _catalog_item_payload(
            intent=intent,
            context=context,
            catalog_item_sys_id=catalog_item_sys_id,
            update_name=update_name,
        ),
        "application": "global",
    }


def _catalog_variable_update(
    *,
    intent: CatalogItemIntent,
    variable: CatalogVariableIntent,
    variable_sys_id: str,
    catalog_item_sys_id: str,
    remote_update_set_sys_id: str,
) -> dict[str, Any]:
    update_name = f"item_option_new_{variable_sys_id}"
    return {
        "name": update_name,
        "remote_update_set": remote_update_set_sys_id,
        "action": "INSERT_OR_UPDATE",
        "type": "Catalog Variable",
        "target_name": f"{intent.name}.{variable.label}",
        "payload": _catalog_variable_payload(
            intent=intent,
            variable=variable,
            variable_sys_id=variable_sys_id,
            catalog_item_sys_id=catalog_item_sys_id,
            update_name=update_name,
        ),
        "application": "global",
    }


def _catalog_category_update(
    *,
    intent: CatalogItemIntent,
    context: CatalogResolvedContext,
    catalog_item_sys_id: str,
    remote_update_set_sys_id: str,
) -> dict[str, Any]:
    relation_sys_id = _stable_sys_id(
        "sc_cat_item_category",
        catalog_item_sys_id,
        context.category.sys_id,
    )
    update_name = f"sc_cat_item_category_{relation_sys_id}"
    return {
        "name": update_name,
        "remote_update_set": remote_update_set_sys_id,
        "action": "INSERT_OR_UPDATE",
        "type": "Catalog Item Category",
        "target_name": f"{intent.name}.{context.category.display}",
        "payload": _catalog_category_payload(
            intent=intent,
            context=context,
            relation_sys_id=relation_sys_id,
            catalog_item_sys_id=catalog_item_sys_id,
            update_name=update_name,
        ),
        "application": "global",
    }


def _connected_content_update(
    *,
    intent: CatalogItemIntent,
    context: CatalogResolvedContext,
    catalog_item_sys_id: str,
    remote_update_set_sys_id: str,
) -> dict[str, Any]:
    relation_sys_id = _stable_sys_id(
        "m2m_connected_content",
        catalog_item_sys_id,
        context.topic.sys_id,
    )
    update_name = f"m2m_connected_content_{relation_sys_id}"
    return {
        "name": update_name,
        "remote_update_set": remote_update_set_sys_id,
        "action": "INSERT_OR_UPDATE",
        "type": "Connected Content",
        "target_name": f"{intent.name}.{context.topic.display}",
        "payload": _connected_content_payload(
            intent=intent,
            context=context,
            relation_sys_id=relation_sys_id,
            catalog_item_sys_id=catalog_item_sys_id,
            update_name=update_name,
        ),
        "application": "global",
    }


def _catalog_item_payload(
    *,
    intent: CatalogItemIntent,
    context: CatalogResolvedContext,
    catalog_item_sys_id: str,
    update_name: str,
) -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<record_update table="sc_cat_item">'
        '<sc_cat_item action="INSERT_OR_UPDATE">'
        "<access_type>restricted</access_type>"
        "<active>true</active>"
        "<availability>on_both</availability>"
        f'<category display_value="{escape(context.category.display)}">'
        f"{escape(context.category.sys_id)}</category>"
        f"<description><![CDATA[{_safe_cdata(intent.description)}]]></description>"
        "<ignore_price>true</ignore_price>"
        "<no_cart>false</no_cart>"
        "<no_order>false</no_order>"
        "<no_quantity>true</no_quantity>"
        f"<name>{escape(intent.name)}</name>"
        "<price>0</price>"
        f"<sc_catalogs>{escape(context.catalog.sys_id)}</sc_catalogs>"
        f"<short_description>{escape(intent.short_description)}</short_description>"
        "<sys_class_name>sc_cat_item</sys_class_name>"
        f"<sys_id>{escape(catalog_item_sys_id)}</sys_id>"
        '<sys_scope display_value="Global">global</sys_scope>'
        f"<sys_update_name>{escape(update_name)}</sys_update_name>"
        f'<taxonomy_topic display_value="{escape(context.topic.display)}">'
        f"{escape(context.topic.sys_id)}</taxonomy_topic>"
        "</sc_cat_item>"
        "</record_update>"
    )


def _catalog_variable_payload(
    *,
    intent: CatalogItemIntent,
    variable: CatalogVariableIntent,
    variable_sys_id: str,
    catalog_item_sys_id: str,
    update_name: str,
) -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<record_update table="item_option_new">'
        '<item_option_new action="INSERT_OR_UPDATE">'
        "<active>true</active>"
        f'<cat_item display_value="{escape(intent.name)}">{escape(catalog_item_sys_id)}</cat_item>'
        f"<default_value>{escape(variable.default_value)}</default_value>"
        f"<help_text>{escape(variable.help_text)}</help_text>"
        f"<mandatory>{_bool_text(variable.mandatory)}</mandatory>"
        f"<name>{escape(variable.name)}</name>"
        f"<order>{variable.order}</order>"
        f"<question_text>{escape(variable.label)}</question_text>"
        f"{_reference_variable_payload(variable)}"
        "<show_help>true</show_help>"
        "<sys_class_name>item_option_new</sys_class_name>"
        f"<sys_id>{escape(variable_sys_id)}</sys_id>"
        '<sys_scope display_value="Global">global</sys_scope>'
        f"<sys_update_name>{escape(update_name)}</sys_update_name>"
        f"<type>{escape(CATALOG_VARIABLE_TYPE_IDS[variable.variable_type])}</type>"
        f"<variable_name>{escape(variable.name)}</variable_name>"
        "</item_option_new>"
        "</record_update>"
    )


def _catalog_category_payload(
    *,
    intent: CatalogItemIntent,
    context: CatalogResolvedContext,
    relation_sys_id: str,
    catalog_item_sys_id: str,
    update_name: str,
) -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<record_update table="sc_cat_item_category">'
        '<sc_cat_item_category action="INSERT_OR_UPDATE">'
        f'<sc_cat_item display_value="{escape(intent.name)}">'
        f"{escape(catalog_item_sys_id)}</sc_cat_item>"
        f'<sc_category display_value="{escape(context.category.display)}">'
        f"{escape(context.category.sys_id)}</sc_category>"
        "<sys_class_name>sc_cat_item_category</sys_class_name>"
        f"<sys_id>{escape(relation_sys_id)}</sys_id>"
        '<sys_scope display_value="Global">global</sys_scope>'
        f"<sys_update_name>{escape(update_name)}</sys_update_name>"
        "</sc_cat_item_category>"
        "</record_update>"
    )


def _connected_content_payload(
    *,
    intent: CatalogItemIntent,
    context: CatalogResolvedContext,
    relation_sys_id: str,
    catalog_item_sys_id: str,
    update_name: str,
) -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<record_update table="m2m_connected_content">'
        '<m2m_connected_content action="INSERT_OR_UPDATE">'
        f'<catalog_item display_value="{escape(intent.name)}">'
        f"{escape(catalog_item_sys_id)}</catalog_item>"
        f"<content_display_value>{escape(intent.name)}</content_display_value>"
        f'<content_type display_value="{escape(context.content_type.display)}">'
        f"{escape(context.content_type.sys_id)}</content_type>"
        "<source>Jedi DevProject</source>"
        "<sys_class_name>m2m_connected_content</sys_class_name>"
        f"<sys_id>{escape(relation_sys_id)}</sys_id>"
        '<sys_scope display_value="Global">global</sys_scope>'
        f"<sys_update_name>{escape(update_name)}</sys_update_name>"
        f'<topic display_value="{escape(context.topic.display)}">'
        f"{escape(context.topic.sys_id)}</topic>"
        "</m2m_connected_content>"
        "</record_update>"
    )


def _reference_variable_payload(variable: CatalogVariableIntent) -> str:
    if variable.variable_type != "reference":
        return ""
    reference_table = variable.reference_table or ""
    reference_qualifier = variable.reference_qualifier or ""
    return (
        f"<reference>{escape(reference_table)}</reference>"
        f"<reference_qual>{escape(reference_qualifier)}</reference_qual>"
        f"<reference_qual_condition>{escape(reference_qualifier)}</reference_qual_condition>"
        f"<use_reference_qualifier>"
        f"{'simple' if reference_qualifier else ''}"
        f"</use_reference_qualifier>"
    )


def _resolve_named_record(
    *,
    records: list[dict[str, Any]],
    display_name: str,
    label: str,
    name_fields: tuple[str, ...],
) -> CatalogResolvedReference:
    matches = [
        record
        for record in records
        if _is_active(record)
        and any(
            _normalize_display(record.get(field)) == _normalize_display(display_name)
            for field in name_fields
        )
    ]
    if not matches:
        raise ValueError(f"{label} was not found: {display_name}")
    if len(matches) > 1:
        raise ValueError(f"{label} is ambiguous: {display_name}")
    return CatalogResolvedReference(
        sys_id=_reference_value(matches[0].get("sys_id")),
        display=_display_from_record(matches[0], name_fields),
    )


def _resolve_category(
    *,
    records: list[dict[str, Any]],
    display_name: str,
    catalog_sys_id: str,
) -> CatalogResolvedReference:
    matches = [
        record
        for record in records
        if _is_active(record)
        and _normalize_display(record.get("title") or record.get("name"))
        == _normalize_display(display_name)
        and _reference_value(record.get("sc_catalog")) == catalog_sys_id
    ]
    if not matches:
        raise ValueError(f"category was not found under catalog: {display_name}")
    if len(matches) > 1:
        raise ValueError(f"category is ambiguous under catalog: {display_name}")
    return CatalogResolvedReference(
        sys_id=_reference_value(matches[0].get("sys_id")),
        display=_display_from_record(matches[0], ("title", "name")),
    )


def _resolve_topic(
    *,
    records: list[dict[str, Any]],
    display_name: str,
    taxonomy_sys_id: str,
) -> CatalogResolvedReference:
    normalized_name = _normalize_display(display_name)
    matches = [
        record
        for record in records
        if _is_active(record)
        and _reference_value(record.get("taxonomy")) == taxonomy_sys_id
        and (
            _normalize_display(record.get("topic_path")) == normalized_name
            or _normalize_display(record.get("name")) == normalized_name
        )
    ]
    if not matches:
        raise ValueError(f"Employee Center topic was not found: {display_name}")
    if len(matches) > 1:
        raise ValueError(f"Employee Center topic is ambiguous: {display_name}")
    return CatalogResolvedReference(
        sys_id=_reference_value(matches[0].get("sys_id")),
        display=_display_from_record(matches[0], ("topic_path", "name")),
    )


def _first_change_fields(changes: list[CandidateChange], table: str) -> dict[str, Any]:
    for change in changes:
        if change.table == table:
            return dict(change.fields)
    return {}


def _normalize_variable_type(value: str) -> str:
    cleaned = value.strip().lower().replace("-", "_").replace(" ", "_")
    aliases = {
        "single_line": "single_line_text",
        "string": "single_line_text",
        "text": "single_line_text",
        "multi_line": "multi_line_text",
        "multiline": "multi_line_text",
        "yes/no": "yes_no",
        "boolean": "yes_no",
    }
    return aliases.get(cleaned, cleaned)


def _normalize_name(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9_]+", "_", value.strip().lower()).strip("_")
    return cleaned


def _stable_sys_id(*parts: str) -> str:
    payload = "|".join(parts)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:32]


def _is_active(record: dict[str, Any]) -> bool:
    return str(record.get("active", "true")).strip().lower() not in {"false", "0", "no"}


def _display_from_record(record: dict[str, Any], fields: tuple[str, ...]) -> str:
    for field in fields:
        value = str(record.get(field) or "").strip()
        if value:
            return value
    return _reference_value(record.get("sys_id"))


def _normalize_display(value: Any) -> str:
    return str(value or "").strip().casefold()


def _reference_value(value: Any) -> str:
    if isinstance(value, dict):
        return str(value.get("value") or value.get("display_value") or "")
    return str(value or "")


def _optional_int(value: Any) -> int | None:
    text = str(value or "").strip()
    return int(text) if text.isdigit() else None


def _bool_value(value: Any) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "required", "mandatory"}


def _bool_text(value: bool) -> str:
    return "true" if value else "false"


def _safe_cdata(value: str) -> str:
    return value.replace("]]>", "]]]]><![CDATA[>")
