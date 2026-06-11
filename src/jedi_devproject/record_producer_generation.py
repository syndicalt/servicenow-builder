"""Deterministic customer-update builder for record producers.

Record producers (``sc_cat_item_producer``, extending ``sc_cat_item``) create a
record in a target table from catalog variables. This builder mirrors the
catalog item builder's structure and conservatism and reuses its variable
machinery (typed variable intents, type ids, reference-qualifier validation,
and the shared ``item_option_new`` payload builder).

Scope is intentionally narrow and script-free:

- one ``sc_cat_item_producer`` insert (name, short description, target table;
  the ``script`` field always renders empty),
- ``item_option_new`` variables, each mapped declaratively to a target-table
  field with ``map_to_field=true`` and ``field`` set to the field name,
- one ``sc_cat_item_category`` placement.

The discovery contract fails closed: the target table must exist
(``sys_db_object``), every mapped field must exist on it (``sys_dictionary``),
and catalog/category resolution reuses the catalog discovery surfaces. Any
producer script request raises with a stable reason code so the story routes
to manual review instead of generating scripted mapping.
"""

from __future__ import annotations

import re
from typing import Any

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from jedi_devproject.catalog_item_generation import (
    CATALOG_VARIABLE_TYPE_IDS,
    CatalogMetadataClient,
    CatalogResolvedReference,
    CatalogVariableIntent,
    _catalog_variable_intent,
    _first_change_fields,
    _item_option_payload,
    _reference_variable_payload,
    _resolve_category,
    _resolve_named_record,
    _stable_sys_id,
)
from jedi_devproject.models import CandidateChange
from jedi_devproject.xml_builder import (
    SYS_SCOPE_GLOBAL,
    cdata,
    container_element,
    record_update,
    text_element,
)

RECORD_PRODUCER_TABLE = "sc_cat_item_producer"

RECORD_PRODUCER_SCRIPT_REASON_CODE = "record_producer:producer_script_manual_review"

_MAPPED_FIELD_NAME_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")


class RecordProducerVariableIntent(CatalogVariableIntent):
    """A record producer variable mapped declaratively to a target-table field."""

    mapped_field: str

    @model_validator(mode="after")
    def require_mapped_field(self) -> RecordProducerVariableIntent:
        cleaned = self.mapped_field.strip()
        if cleaned == "":
            raise ValueError(
                f"record producer variable {self.name} requires a target field mapping"
            )
        if _MAPPED_FIELD_NAME_PATTERN.fullmatch(cleaned) is None:
            raise ValueError(
                f"record producer mapped field is not a valid field name: {cleaned}"
            )
        self.mapped_field = cleaned
        return self


class RecordProducerIntent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    short_description: str
    description: str = ""
    table_name: str
    catalog: str
    category: str
    variables: list[RecordProducerVariableIntent]

    @field_validator("name", "short_description", "table_name", "catalog", "category")
    @classmethod
    def require_text(cls, value: str) -> str:
        cleaned = value.strip()
        if cleaned == "":
            raise ValueError("must not be empty")
        return cleaned

    @model_validator(mode="after")
    def require_mapped_variables(self) -> RecordProducerIntent:
        if not self.variables:
            raise ValueError("record producer requires at least one variable")
        names = [variable.name for variable in self.variables]
        if len(set(names)) != len(names):
            raise ValueError("record producer variable names must be unique")
        mapped_fields = [variable.mapped_field for variable in self.variables]
        duplicates = sorted(
            {field for field in mapped_fields if mapped_fields.count(field) > 1}
        )
        if duplicates:
            raise ValueError(
                "record producer maps a target field more than once: "
                f"{', '.join(duplicates)}"
            )
        return self


class RecordProducerResolvedContext(BaseModel):
    model_config = ConfigDict(extra="forbid")

    catalog: CatalogResolvedReference
    category: CatalogResolvedReference


def record_producer_customer_updates(
    *,
    client: CatalogMetadataClient,
    changes: list[CandidateChange],
    remote_update_set_sys_id: str,
) -> list[dict[str, Any]]:
    intent = _record_producer_intent(changes)
    _require_target_table(client=client, table_name=intent.table_name)
    _require_mapped_fields(client=client, intent=intent)
    context = _resolve_record_producer_context(client=client, intent=intent)
    producer_sys_id = _stable_sys_id(RECORD_PRODUCER_TABLE, intent.name)
    return [
        _record_producer_update(
            intent=intent,
            context=context,
            producer_sys_id=producer_sys_id,
            remote_update_set_sys_id=remote_update_set_sys_id,
        ),
        *[
            _producer_variable_update(
                intent=intent,
                variable=variable,
                producer_sys_id=producer_sys_id,
                remote_update_set_sys_id=remote_update_set_sys_id,
            )
            for variable in intent.variables
        ],
        _producer_category_update(
            intent=intent,
            context=context,
            producer_sys_id=producer_sys_id,
            remote_update_set_sys_id=remote_update_set_sys_id,
        ),
    ]


def _record_producer_intent(changes: list[CandidateChange]) -> RecordProducerIntent:
    producer_change = next(
        (change for change in changes if change.table == RECORD_PRODUCER_TABLE), None
    )
    if producer_change is None:
        raise ValueError("Record Producer handoff requires one sc_cat_item_producer change")
    if producer_change.operation != "insert":
        raise ValueError("Record Producer handoff supports insert only")
    producer_fields = dict(producer_change.fields)
    if str(producer_fields.get("script") or "").strip():
        raise ValueError(
            "record producer scripts are unsupported and route to manual review "
            f"({RECORD_PRODUCER_SCRIPT_REASON_CODE})"
        )
    category_fields = _first_change_fields(changes, "sc_cat_item_category")
    variables = [
        _record_producer_variable_intent(change)
        for change in changes
        if change.table == "item_option_new"
    ]
    return RecordProducerIntent(
        name=str(producer_fields.get("name") or producer_fields.get("artifact_name") or ""),
        short_description=str(producer_fields.get("short_description") or ""),
        description=str(producer_fields.get("description") or ""),
        table_name=str(
            producer_fields.get("table_name") or producer_fields.get("target_table") or ""
        ),
        catalog=str(producer_fields.get("catalog") or category_fields.get("catalog") or ""),
        category=str(producer_fields.get("category") or category_fields.get("category") or ""),
        variables=variables,
    )


def _record_producer_variable_intent(change: CandidateChange) -> RecordProducerVariableIntent:
    if change.operation != "insert":
        raise ValueError("Record Producer variable handoff supports insert only")
    base = _catalog_variable_intent(change)
    fields = dict(change.fields)
    mapped_field = str(fields.get("field") or fields.get("mapped_field") or "")
    return RecordProducerVariableIntent(**base.model_dump(), mapped_field=mapped_field)


def _require_target_table(*, client: CatalogMetadataClient, table_name: str) -> None:
    records = client.fetch_table_records(
        table="sys_db_object",
        lookup={"name": table_name},
        fields=["name", "label"],
        limit=1,
    )
    if not records:
        raise ValueError(f"record producer target table was not found: {table_name}")


def _require_mapped_fields(
    *,
    client: CatalogMetadataClient,
    intent: RecordProducerIntent,
) -> None:
    records = client.fetch_table_records(
        table="sys_dictionary",
        lookup={"name": intent.table_name},
        fields=["element", "internal_type"],
        limit=500,
    )
    elements = {
        str(record.get("element") or "").strip()
        for record in records
        if str(record.get("element") or "").strip()
    }
    for variable in intent.variables:
        if variable.mapped_field not in elements:
            raise ValueError(
                "record producer mapped field was not found on "
                f"{intent.table_name}: {variable.mapped_field}"
            )


def _resolve_record_producer_context(
    *,
    client: CatalogMetadataClient,
    intent: RecordProducerIntent,
) -> RecordProducerResolvedContext:
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
    return RecordProducerResolvedContext(catalog=catalog, category=category)


def _record_producer_update(
    *,
    intent: RecordProducerIntent,
    context: RecordProducerResolvedContext,
    producer_sys_id: str,
    remote_update_set_sys_id: str,
) -> dict[str, Any]:
    update_name = f"sc_cat_item_producer_{producer_sys_id}"
    return {
        "name": update_name,
        "remote_update_set": remote_update_set_sys_id,
        "action": "INSERT_OR_UPDATE",
        "type": "Record Producer",
        "target_name": intent.name,
        "payload": _record_producer_payload(
            intent=intent,
            context=context,
            producer_sys_id=producer_sys_id,
            update_name=update_name,
        ),
        "application": "global",
    }


def _record_producer_payload(
    *,
    intent: RecordProducerIntent,
    context: RecordProducerResolvedContext,
    producer_sys_id: str,
    update_name: str,
) -> str:
    return record_update(
        container_element(
            RECORD_PRODUCER_TABLE,
            "<active>true</active>",
            text_element(
                "category",
                context.category.sys_id,
                display_value=context.category.display,
            ),
            container_element("description", cdata(intent.description)),
            text_element("name", intent.name),
            text_element("sc_catalogs", context.catalog.sys_id),
            container_element("script", cdata("")),
            text_element("short_description", intent.short_description),
            f"<sys_class_name>{RECORD_PRODUCER_TABLE}</sys_class_name>",
            text_element("sys_id", producer_sys_id),
            SYS_SCOPE_GLOBAL,
            text_element("sys_update_name", update_name),
            text_element("table_name", intent.table_name),
            action="INSERT_OR_UPDATE",
        ),
        table=RECORD_PRODUCER_TABLE,
    )


def _producer_variable_update(
    *,
    intent: RecordProducerIntent,
    variable: RecordProducerVariableIntent,
    producer_sys_id: str,
    remote_update_set_sys_id: str,
) -> dict[str, Any]:
    variable_sys_id = _stable_sys_id(
        RECORD_PRODUCER_TABLE, "item_option_new", intent.name, variable.name
    )
    update_name = f"item_option_new_{variable_sys_id}"
    return {
        "name": update_name,
        "remote_update_set": remote_update_set_sys_id,
        "action": "INSERT_OR_UPDATE",
        "type": "Record Producer Variable",
        "target_name": f"{intent.name}.{variable.label}",
        "payload": _item_option_payload(
            item_name=intent.name,
            name=variable.name,
            label=variable.label,
            type_id=CATALOG_VARIABLE_TYPE_IDS[variable.variable_type],
            order=variable.order,
            mandatory=variable.mandatory,
            default_value=variable.default_value,
            help_text=variable.help_text,
            reference_part=_reference_variable_payload(variable),
            variable_sys_id=variable_sys_id,
            catalog_item_sys_id=producer_sys_id,
            update_name=update_name,
            field_part=text_element("field", variable.mapped_field),
            mapping_part="<map_to_field>true</map_to_field>",
        ),
        "application": "global",
    }


def _producer_category_update(
    *,
    intent: RecordProducerIntent,
    context: RecordProducerResolvedContext,
    producer_sys_id: str,
    remote_update_set_sys_id: str,
) -> dict[str, Any]:
    relation_sys_id = _stable_sys_id(
        "sc_cat_item_category",
        producer_sys_id,
        context.category.sys_id,
    )
    update_name = f"sc_cat_item_category_{relation_sys_id}"
    return {
        "name": update_name,
        "remote_update_set": remote_update_set_sys_id,
        "action": "INSERT_OR_UPDATE",
        "type": "Record Producer Category",
        "target_name": f"{intent.name}.{context.category.display}",
        "payload": _producer_category_payload(
            intent=intent,
            context=context,
            relation_sys_id=relation_sys_id,
            producer_sys_id=producer_sys_id,
            update_name=update_name,
        ),
        "application": "global",
    }


def _producer_category_payload(
    *,
    intent: RecordProducerIntent,
    context: RecordProducerResolvedContext,
    relation_sys_id: str,
    producer_sys_id: str,
    update_name: str,
) -> str:
    return record_update(
        container_element(
            "sc_cat_item_category",
            text_element("sc_cat_item", producer_sys_id, display_value=intent.name),
            text_element(
                "sc_category",
                context.category.sys_id,
                display_value=context.category.display,
            ),
            "<sys_class_name>sc_cat_item_category</sys_class_name>",
            text_element("sys_id", relation_sys_id),
            SYS_SCOPE_GLOBAL,
            text_element("sys_update_name", update_name),
            action="INSERT_OR_UPDATE",
        ),
        table="sc_cat_item_category",
    )
