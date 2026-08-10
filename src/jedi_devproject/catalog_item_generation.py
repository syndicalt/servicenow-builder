from __future__ import annotations

import hashlib
import re
from typing import Any, Protocol

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from jedi_devproject.catalog_client_script_generation import (
    CATALOG_CLIENT_SCRIPT_TABLE,
    catalog_client_script_customer_updates,
)
from jedi_devproject.catalog_ui_policy_generation import (
    CATALOG_UI_POLICY_TABLES,
    catalog_ui_policy_customer_updates,
)
from jedi_devproject.discovery.flows import resolve_fulfillment_flow
from jedi_devproject.models import CandidateChange
from jedi_devproject.validation_helpers import TRUTHY_TOKENS, bool_value, optional_int, slug
from jedi_devproject.xml_builder import (
    SYS_SCOPE_GLOBAL,
    bool_element,
    cdata,
    container_element,
    record_update,
    reference_qualifier_elements,
    text_element,
)


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
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    sys_id: str
    display: str


REFERENCE_QUALIFIER_MAX_LENGTH = 255
CATALOG_ITEM_FIELD_NON_JSON_DIAGNOSTIC = (
    "catalog item generation field contains non-JSON value"
)
CATALOG_ITEM_METADATA_MISSING_DIAGNOSTIC = "catalog item metadata field is missing"

_QUALIFIER_SCRIPT_INDICATOR_PATTERN = re.compile(
    r"javascript:|\bgs\s*\.|\bcurrent\s*\.|[;(){}]",
    re.IGNORECASE,
)
_QUALIFIER_CONDITION_PATTERN = re.compile(
    r"^(?P<field>[a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*){0,2})"
    r"(?P<operator>ISNOTEMPTY|ISEMPTY|STARTSWITH|ENDSWITH|NOT LIKE|NOT IN|LIKE|IN|!=|>=|<=|=|>|<)"
    r"(?P<value>.*)$"
)
_QUALIFIER_UNARY_OPERATORS = frozenset({"ISEMPTY", "ISNOTEMPTY"})


def validated_reference_qualifier(qualifier: str) -> str:
    """Validate a declarative encoded-query reference qualifier and return it.

    Allowed grammar (everything else fails closed with ``ValueError``)::

        qualifier := condition ( ("^" | "^OR") condition )*
        condition := field operator value | field unary-operator
        field     := segment ( "." segment )*        (at most three segments)
        segment   := [a-z][a-z0-9_]*                 (plausible ServiceNow field name)
        operator  := "=" | "!=" | ">" | ">=" | "<" | "<=" | "IN" | "NOT IN"
                     | "LIKE" | "NOT LIKE" | "STARTSWITH" | "ENDSWITH"
        unary-operator := "ISEMPTY" | "ISNOTEMPTY"   (carries no value)
        value     := non-empty text without script indicators

    Script indicators are rejected anywhere in the qualifier: ``javascript:``,
    ``gs.``, ``current.``, semicolons, parentheses, and braces. Dynamic
    filters, scripted qualifiers, and anything that is not a simple
    field-operator-value encoded query are therefore rejected. An empty
    qualifier is allowed and normalizes to the empty string.
    """
    cleaned = qualifier.strip()
    if not cleaned:
        return ""
    if len(cleaned) > REFERENCE_QUALIFIER_MAX_LENGTH:
        raise ValueError(
            f"reference qualifier exceeds {REFERENCE_QUALIFIER_MAX_LENGTH} characters"
        )
    indicator = _QUALIFIER_SCRIPT_INDICATOR_PATTERN.search(cleaned)
    if indicator is not None:
        raise ValueError(
            f"reference qualifier contains script indicator: {indicator.group(0)}"
        )
    for index, raw_condition in enumerate(cleaned.split("^")):
        condition = raw_condition
        if index > 0 and condition.startswith("OR"):
            condition = condition[2:]
        match = _QUALIFIER_CONDITION_PATTERN.fullmatch(condition)
        if match is None:
            raise ValueError(
                "reference qualifier is not a declarative field-operator-value "
                f"encoded query: {raw_condition}"
            )
        operator = match.group("operator")
        value = match.group("value")
        if operator in _QUALIFIER_UNARY_OPERATORS and value:
            raise ValueError(
                f"reference qualifier operator {operator} must not carry a value"
            )
        if operator not in _QUALIFIER_UNARY_OPERATORS and not value:
            raise ValueError(
                f"reference qualifier condition is missing a value: {raw_condition}"
            )
    return cleaned


def is_declarative_reference_qualifier(qualifier: str) -> bool:
    try:
        validated_reference_qualifier(qualifier)
    except ValueError:
        return False
    return True


class CatalogVariableGroup(BaseModel):
    """A titled container section grouping the item's own new variables."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    title: str
    variables: list[str]

    @field_validator("title")
    @classmethod
    def require_title(cls, value: str) -> str:
        cleaned = value.strip()
        if cleaned == "":
            raise ValueError("must not be empty")
        return cleaned

    @model_validator(mode="after")
    def require_members(self) -> CatalogVariableGroup:
        members = [member.strip() for member in self.variables]
        if not members or any(member == "" for member in members):
            raise ValueError(
                f"catalog variable group {self.title} requires at least one member variable"
            )
        if len(set(members)) != len(members):
            raise ValueError(
                f"catalog variable group {self.title} lists a member variable twice"
            )
        self.variables = members
        return self

    @property
    def container_start_name(self) -> str:
        return f"{slug(self.title, default='group')}_container"

    @property
    def container_end_name(self) -> str:
        return f"{slug(self.title, default='group')}_container_end"


class CatalogVariableIntent(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

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
        if self.reference_qualifier:
            try:
                self.reference_qualifier = validated_reference_qualifier(self.reference_qualifier)
            except ValueError as error:
                raise ValueError(
                    f"reference qualifier rejected for {self.name}: {error}"
                ) from None
        return self


class CatalogItemIntent(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    name: str
    short_description: str
    description: str = ""
    catalog: str
    category: str
    taxonomy: str
    employee_center_topic: str
    variables: list[CatalogVariableIntent]
    variable_sets: list[str] = Field(default_factory=list)
    variable_groups: list[CatalogVariableGroup] = Field(default_factory=list)
    # Name of an EXISTING, ACTIVE, record-triggered flow to attach as the
    # item's fulfillment flow (sc_cat_item.flow_designer_flow). Resolution is
    # live and fail-closed; flow creation or modification is never represented
    # here.
    fulfillment_flow: str | None = None

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
        self._require_valid_variable_sets()
        self._require_valid_variable_groups(set(names))
        return self

    def _require_valid_variable_sets(self) -> None:
        cleaned = [name.strip() for name in self.variable_sets]
        if any(name == "" for name in cleaned):
            raise ValueError("catalog variable set names must not be empty")
        normalized = [name.casefold() for name in cleaned]
        if len(set(normalized)) != len(normalized):
            raise ValueError("catalog variable set names must be unique")
        self.variable_sets = cleaned

    def _require_valid_variable_groups(self, variable_names: set[str]) -> None:
        if not self.variable_groups:
            return
        titles = [group.title.casefold() for group in self.variable_groups]
        if len(set(titles)) != len(titles):
            raise ValueError("catalog variable group titles must be unique")
        grouped: set[str] = set()
        container_names: set[str] = set()
        for group in self.variable_groups:
            for member in group.variables:
                if member not in variable_names:
                    raise ValueError(
                        f"catalog variable group {group.title} references "
                        f"unknown variable: {member}"
                    )
                if member in grouped:
                    raise ValueError(
                        f"catalog variable {member} is assigned to more than one group"
                    )
                grouped.add(member)
            container_names.update({group.container_start_name, group.container_end_name})
        if len(container_names) != 2 * len(self.variable_groups):
            raise ValueError("catalog variable group titles must produce unique container names")
        collisions = container_names & variable_names
        if collisions:
            raise ValueError(
                "catalog variable group container names collide with variables: "
                f"{', '.join(sorted(collisions))}"
            )


class CatalogResolvedContext(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    catalog: CatalogResolvedReference
    category: CatalogResolvedReference
    taxonomy: CatalogResolvedReference
    topic: CatalogResolvedReference
    content_type: CatalogResolvedReference
    variable_sets: list[CatalogResolvedReference] = Field(default_factory=list)
    fulfillment_flow: CatalogResolvedReference | None = None


CATALOG_VARIABLE_TYPE_IDS = {
    "yes_no": "1",
    "multi_line_text": "2",
    "checkbox": "7",
    "reference": "8",
    "date": "9",
    "single_line_text": "6",
}

# item_option_new container rows are generated only from validated variable
# groups; stories cannot request these types directly through Variables.
CATALOG_CONTAINER_TYPE_IDS = {
    "container_start": "19",
    "container_end": "20",
}

_MANDATORY_TRUTHY_TOKENS = TRUTHY_TOKENS | {"required", "mandatory"}


def catalog_item_customer_updates(
    *,
    client: CatalogMetadataClient,
    changes: list[CandidateChange],
    remote_update_set_sys_id: str,
) -> list[dict[str, Any]]:
    intent = _catalog_item_intent(changes)
    context = _resolve_catalog_context(client=client, intent=intent)
    catalog_item_sys_id = _stable_sys_id("sc_cat_item", intent.name)
    return [
        _catalog_item_update(
            intent=intent,
            context=context,
            catalog_item_sys_id=catalog_item_sys_id,
            remote_update_set_sys_id=remote_update_set_sys_id,
        ),
        *_catalog_variable_updates(
            intent=intent,
            catalog_item_sys_id=catalog_item_sys_id,
            remote_update_set_sys_id=remote_update_set_sys_id,
        ),
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
        *[
            _variable_set_link_update(
                intent=intent,
                variable_set=variable_set,
                catalog_item_sys_id=catalog_item_sys_id,
                remote_update_set_sys_id=remote_update_set_sys_id,
            )
            for variable_set in context.variable_sets
        ],
        *_variable_behavior_updates(
            intent=intent,
            changes=changes,
            catalog_item_sys_id=catalog_item_sys_id,
            remote_update_set_sys_id=remote_update_set_sys_id,
        ),
    ]


def _variable_behavior_updates(
    *,
    intent: CatalogItemIntent,
    changes: list[CandidateChange],
    catalog_item_sys_id: str,
    remote_update_set_sys_id: str,
) -> list[dict[str, Any]]:
    """Render catalog UI policy and catalog client script updates, if requested.

    Stories without variable behavior contribute no changes here, so their
    catalog payloads stay byte-identical. Behavior changes may only reference
    the item's OWN generated variables; the delegated builders fail closed on
    anything else.
    """
    policy_changes = [change for change in changes if change.table in CATALOG_UI_POLICY_TABLES]
    script_changes = [
        change for change in changes if change.table == CATALOG_CLIENT_SCRIPT_TABLE
    ]
    if not policy_changes and not script_changes:
        return []
    variable_sys_ids = {
        variable.name: _stable_sys_id("item_option_new", intent.name, variable.name)
        for variable in intent.variables
    }
    updates: list[dict[str, Any]] = []
    if policy_changes:
        updates.extend(
            catalog_ui_policy_customer_updates(
                changes=policy_changes,
                remote_update_set_sys_id=remote_update_set_sys_id,
                catalog_item_name=intent.name,
                catalog_item_sys_id=catalog_item_sys_id,
                variable_sys_ids=variable_sys_ids,
            )
        )
    if script_changes:
        updates.extend(
            catalog_client_script_customer_updates(
                changes=script_changes,
                remote_update_set_sys_id=remote_update_set_sys_id,
                catalog_item_name=intent.name,
                catalog_item_sys_id=catalog_item_sys_id,
                item_variable_names=set(variable_sys_ids),
            )
        )
    return updates


def _catalog_variable_updates(
    *,
    intent: CatalogItemIntent,
    catalog_item_sys_id: str,
    remote_update_set_sys_id: str,
) -> list[dict[str, Any]]:
    """Render variable rows, interleaving container start/end rows for groups.

    Without groups the variables render exactly as declared (payloads stay
    byte-identical to the ungrouped builder). With groups, rows are emitted in
    declaration order, each group expands in place at its first member, every
    container is closed, and ``order`` is re-sequenced 100, 200, ... across the
    interleaved rows so review order matches render order.
    """
    if not intent.variable_groups:
        return [
            _catalog_variable_update(
                intent=intent,
                variable=variable,
                variable_sys_id=_stable_sys_id("item_option_new", intent.name, variable.name),
                catalog_item_sys_id=catalog_item_sys_id,
                remote_update_set_sys_id=remote_update_set_sys_id,
            )
            for variable in intent.variables
        ]
    group_for_member = {
        member: group for group in intent.variable_groups for member in group.variables
    }
    variables_by_name = {variable.name: variable for variable in intent.variables}
    updates: list[dict[str, Any]] = []
    emitted: set[str] = set()
    position = 0
    for variable in intent.variables:
        if variable.name in emitted:
            continue
        group = group_for_member.get(variable.name)
        if group is None:
            position += 1
            updates.append(
                _catalog_variable_update(
                    intent=intent,
                    variable=variable.model_copy(update={"order": position * 100}),
                    variable_sys_id=_stable_sys_id(
                        "item_option_new", intent.name, variable.name
                    ),
                    catalog_item_sys_id=catalog_item_sys_id,
                    remote_update_set_sys_id=remote_update_set_sys_id,
                )
            )
            continue
        position += 1
        updates.append(
            _container_variable_update(
                intent=intent,
                group=group,
                container_kind="container_start",
                order=position * 100,
                catalog_item_sys_id=catalog_item_sys_id,
                remote_update_set_sys_id=remote_update_set_sys_id,
            )
        )
        for member_name in group.variables:
            emitted.add(member_name)
            position += 1
            updates.append(
                _catalog_variable_update(
                    intent=intent,
                    variable=variables_by_name[member_name].model_copy(
                        update={"order": position * 100}
                    ),
                    variable_sys_id=_stable_sys_id(
                        "item_option_new", intent.name, member_name
                    ),
                    catalog_item_sys_id=catalog_item_sys_id,
                    remote_update_set_sys_id=remote_update_set_sys_id,
                )
            )
        position += 1
        updates.append(
            _container_variable_update(
                intent=intent,
                group=group,
                container_kind="container_end",
                order=position * 100,
                catalog_item_sys_id=catalog_item_sys_id,
                remote_update_set_sys_id=remote_update_set_sys_id,
            )
        )
    return updates


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
        name=_catalog_first_text(item_fields.get("name"), item_fields.get("artifact_name")),
        short_description=_catalog_first_text(item_fields.get("short_description")),
        description=_catalog_first_text(item_fields.get("description")),
        catalog=_catalog_first_text(
            item_fields.get("catalog"),
            category_fields.get("catalog"),
        ),
        category=_catalog_first_text(
            item_fields.get("category"),
            category_fields.get("category"),
        ),
        taxonomy=_catalog_first_text(
            item_fields.get("taxonomy"),
            topic_fields.get("taxonomy"),
        ),
        employee_center_topic=_catalog_first_text(
            item_fields.get("employee_center_topic"),
            item_fields.get("topic"),
            topic_fields.get("topic"),
            topic_fields.get("employee_center_topic"),
        ),
        variables=variables,
        variable_sets=_variable_set_names(item_fields.get("variable_sets")),
        variable_groups=_variable_group_intents(item_fields.get("variable_groups")),
        fulfillment_flow=_catalog_first_text(item_fields.get("fulfillment_flow")).strip()
        or None,
    )


def _variable_set_names(value: Any) -> list[str]:
    if value is None:
        return []
    if type(value) is list:
        return [text for item in value if (text := _catalog_field_text(item).strip())]
    return [
        part.strip()
        for part in re.split(r"[;,]", _catalog_field_text(value))
        if part.strip()
    ]


def _variable_group_intents(value: Any) -> list[CatalogVariableGroup]:
    if value is None:
        return []
    if type(value) is list:
        groups: list[CatalogVariableGroup] = []
        for item in value:
            if isinstance(item, CatalogVariableGroup):
                groups.append(item)
            elif type(item) is dict:
                groups.append(CatalogVariableGroup.model_validate(item))
            else:
                raise ValueError("catalog variable group must be an object")
        return groups
    groups = []
    for raw_entry in _catalog_field_text(value).split(";"):
        entry = raw_entry.strip()
        if not entry:
            continue
        title, _, raw_members = entry.partition("|")
        groups.append(
            CatalogVariableGroup(
                title=title.strip(),
                variables=[
                    slug(member, default="")
                    for member in raw_members.split(",")
                    if member.strip()
                ],
            )
        )
    return groups


def _catalog_variable_intent(change: CandidateChange) -> CatalogVariableIntent:
    if change.operation != "insert":
        raise ValueError("Catalog Item variable handoff supports insert only")
    fields = dict(change.fields)
    variable_type = _normalize_variable_type(_catalog_first_text(fields.get("type")))
    return CatalogVariableIntent(
        name=slug(
            _catalog_first_text(fields.get("name"), fields.get("variable_name")),
            default="",
        ),
        label=_catalog_first_text(fields.get("question_text"), fields.get("label")),
        variable_type=variable_type,
        order=optional_int(_catalog_first_text(fields.get("order"))) or 100,
        mandatory=bool_value(
            _catalog_first_text(fields.get("mandatory")),
            truthy=_MANDATORY_TRUTHY_TOKENS,
        ),
        reference_table=_catalog_first_text(
            fields.get("reference"),
            fields.get("reference_table"),
        ),
        reference_qualifier=_catalog_first_text(
            fields.get("reference_qualifier")
            ,
            fields.get("reference_qual"),
            fields.get("reference_qual_condition"),
        ),
        default_value=_catalog_first_text(fields.get("default_value")),
        help_text=_catalog_first_text(fields.get("help_text")),
    )


def _resolve_catalog_context(
    *,
    client: CatalogMetadataClient,
    intent: CatalogItemIntent,
) -> CatalogResolvedContext:
    catalogs = _catalog_metadata_records(
        client.fetch_table_records(
            table="sc_catalog",
            lookup={},
            fields=["sys_id", "title", "active"],
            limit=100,
        )
    )
    catalog = _resolve_named_record(
        records=catalogs,
        display_name=intent.catalog,
        label="catalog",
        name_fields=("title", "name"),
    )
    categories = _catalog_metadata_records(
        client.fetch_table_records(
            table="sc_category",
            lookup={},
            fields=["sys_id", "title", "active", "sc_catalog"],
            limit=250,
        )
    )
    category = _resolve_category(
        records=categories,
        display_name=intent.category,
        catalog_sys_id=catalog.sys_id,
    )
    taxonomies = _catalog_metadata_records(
        client.fetch_table_records(
            table="taxonomy",
            lookup={},
            fields=["sys_id", "name", "active"],
            limit=100,
        )
    )
    taxonomy = _resolve_named_record(
        records=taxonomies,
        display_name=intent.taxonomy,
        label="taxonomy",
        name_fields=("name",),
    )
    topics = _catalog_metadata_records(
        client.fetch_table_records(
            table="topic",
            lookup={},
            fields=["sys_id", "name", "topic_path", "active", "taxonomy"],
            limit=250,
        )
    )
    topic = _resolve_topic(
        records=topics,
        display_name=intent.employee_center_topic,
        taxonomy_sys_id=taxonomy.sys_id,
    )
    content_types = _catalog_metadata_records(
        client.fetch_table_records(
            table="taxonomy_content_configuration",
            lookup={},
            fields=["sys_id", "name", "active"],
            limit=100,
        )
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
        variable_sets=_resolve_variable_sets(client=client, intent=intent),
        fulfillment_flow=_resolve_fulfillment_flow_reference(client=client, intent=intent),
    )


def _resolve_fulfillment_flow_reference(
    *,
    client: CatalogMetadataClient,
    intent: CatalogItemIntent,
) -> CatalogResolvedReference | None:
    """Resolve the named fulfillment flow live, or skip entirely when unused.

    Stories without a fulfillment flow never touch the flow surface, so their
    payloads stay byte-identical. Resolution fails closed with the stable
    ``fulfillment_flow:*`` reason codes from ``discovery.flows``.
    """
    if intent.fulfillment_flow is None:
        return None
    resolved = resolve_fulfillment_flow(client=client, flow_name=intent.fulfillment_flow)
    return CatalogResolvedReference(sys_id=resolved.sys_id, display=resolved.name)


def _resolve_variable_sets(
    *,
    client: CatalogMetadataClient,
    intent: CatalogItemIntent,
) -> list[CatalogResolvedReference]:
    if not intent.variable_sets:
        return []
    records = _catalog_metadata_records(
        client.fetch_table_records(
            table="item_option_new_set",
            lookup={},
            fields=["sys_id", "title", "internal_name", "active"],
            limit=250,
        )
    )
    return [
        _resolve_named_record(
            records=records,
            display_name=name,
            label="catalog variable set",
            name_fields=("title", "internal_name", "name"),
        )
        for name in intent.variable_sets
    ]


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
    return record_update(
        container_element(
            "sc_cat_item",
            "<access_type>restricted</access_type>",
            "<active>true</active>",
            "<availability>on_both</availability>",
            text_element(
                "category",
                context.category.sys_id,
                display_value=context.category.display,
            ),
            container_element("description", cdata(intent.description)),
            _fulfillment_flow_element(context),
            "<ignore_price>true</ignore_price>",
            "<no_cart>false</no_cart>",
            "<no_order>false</no_order>",
            "<no_quantity>true</no_quantity>",
            text_element("name", intent.name),
            "<price>0</price>",
            text_element("sc_catalogs", context.catalog.sys_id),
            text_element("short_description", intent.short_description),
            "<sys_class_name>sc_cat_item</sys_class_name>",
            text_element("sys_id", catalog_item_sys_id),
            SYS_SCOPE_GLOBAL,
            text_element("sys_update_name", update_name),
            text_element(
                "taxonomy_topic",
                context.topic.sys_id,
                display_value=context.topic.display,
            ),
            action="INSERT_OR_UPDATE",
        ),
        table="sc_cat_item",
    )


def _fulfillment_flow_element(context: CatalogResolvedContext) -> str:
    """Render the sc_cat_item flow reference, or nothing when no flow attaches.

    The empty string keeps payloads byte-identical for stories that do not
    attach a fulfillment flow.
    """
    if context.fulfillment_flow is None:
        return ""
    return text_element(
        "flow_designer_flow",
        context.fulfillment_flow.sys_id,
        display_value=context.fulfillment_flow.display,
    )


def _catalog_variable_payload(
    *,
    intent: CatalogItemIntent,
    variable: CatalogVariableIntent,
    variable_sys_id: str,
    catalog_item_sys_id: str,
    update_name: str,
) -> str:
    return _item_option_payload(
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
        catalog_item_sys_id=catalog_item_sys_id,
        update_name=update_name,
    )


def _container_variable_update(
    *,
    intent: CatalogItemIntent,
    group: CatalogVariableGroup,
    container_kind: str,
    order: int,
    catalog_item_sys_id: str,
    remote_update_set_sys_id: str,
) -> dict[str, Any]:
    name = (
        group.container_start_name
        if container_kind == "container_start"
        else group.container_end_name
    )
    variable_sys_id = _stable_sys_id("item_option_new", intent.name, name)
    update_name = f"item_option_new_{variable_sys_id}"
    is_start = container_kind == "container_start"
    target_suffix = group.title if is_start else f"{group.title} (container end)"
    return {
        "name": update_name,
        "remote_update_set": remote_update_set_sys_id,
        "action": "INSERT_OR_UPDATE",
        "type": "Catalog Variable",
        "target_name": f"{intent.name}.{target_suffix}",
        "payload": _item_option_payload(
            item_name=intent.name,
            name=name,
            label=group.title if is_start else "",
            type_id=CATALOG_CONTAINER_TYPE_IDS[container_kind],
            order=order,
            mandatory=False,
            default_value="",
            help_text="",
            reference_part="",
            variable_sys_id=variable_sys_id,
            catalog_item_sys_id=catalog_item_sys_id,
            update_name=update_name,
        ),
        "application": "global",
    }


def _item_option_payload(
    *,
    item_name: str,
    name: str,
    label: str,
    type_id: str,
    order: int,
    mandatory: bool,
    default_value: str,
    help_text: str,
    reference_part: str,
    variable_sys_id: str,
    catalog_item_sys_id: str,
    update_name: str,
    field_part: str = "",
    mapping_part: str = "",
) -> str:
    """Render one item_option_new customer-update payload.

    Shared by catalog items and record producers: ``field_part`` and
    ``mapping_part`` carry the record-producer field-mapping elements and
    default to empty strings, so catalog item payloads stay byte-identical.
    """
    return record_update(
        container_element(
            "item_option_new",
            "<active>true</active>",
            text_element("cat_item", catalog_item_sys_id, display_value=item_name),
            text_element("default_value", default_value),
            field_part,
            text_element("help_text", help_text),
            bool_element("mandatory", mandatory),
            mapping_part,
            text_element("name", name),
            text_element("order", str(order)),
            text_element("question_text", label),
            reference_part,
            "<show_help>true</show_help>",
            "<sys_class_name>item_option_new</sys_class_name>",
            text_element("sys_id", variable_sys_id),
            SYS_SCOPE_GLOBAL,
            text_element("sys_update_name", update_name),
            text_element("type", type_id),
            text_element("variable_name", name),
            "<visible_bundle>true</visible_bundle>",
            "<visible_standalone>true</visible_standalone>",
            "<visible_summary>true</visible_summary>",
            action="INSERT_OR_UPDATE",
        ),
        table="item_option_new",
    )


def _variable_set_link_update(
    *,
    intent: CatalogItemIntent,
    variable_set: CatalogResolvedReference,
    catalog_item_sys_id: str,
    remote_update_set_sys_id: str,
) -> dict[str, Any]:
    relation_sys_id = _stable_sys_id("io_set_item", catalog_item_sys_id, variable_set.sys_id)
    update_name = f"io_set_item_{relation_sys_id}"
    return {
        "name": update_name,
        "remote_update_set": remote_update_set_sys_id,
        "action": "INSERT_OR_UPDATE",
        "type": "Catalog Variable Set Link",
        "target_name": f"{intent.name}.{variable_set.display}",
        "payload": _variable_set_link_payload(
            intent=intent,
            variable_set=variable_set,
            relation_sys_id=relation_sys_id,
            catalog_item_sys_id=catalog_item_sys_id,
            update_name=update_name,
        ),
        "application": "global",
    }


def _variable_set_link_payload(
    *,
    intent: CatalogItemIntent,
    variable_set: CatalogResolvedReference,
    relation_sys_id: str,
    catalog_item_sys_id: str,
    update_name: str,
) -> str:
    return record_update(
        container_element(
            "io_set_item",
            text_element("sc_cat_item", catalog_item_sys_id, display_value=intent.name),
            "<sys_class_name>io_set_item</sys_class_name>",
            text_element("sys_id", relation_sys_id),
            SYS_SCOPE_GLOBAL,
            text_element("sys_update_name", update_name),
            text_element(
                "variable_set",
                variable_set.sys_id,
                display_value=variable_set.display,
            ),
            action="INSERT_OR_UPDATE",
        ),
        table="io_set_item",
    )


def _catalog_category_payload(
    *,
    intent: CatalogItemIntent,
    context: CatalogResolvedContext,
    relation_sys_id: str,
    catalog_item_sys_id: str,
    update_name: str,
) -> str:
    return record_update(
        container_element(
            "sc_cat_item_category",
            text_element("sc_cat_item", catalog_item_sys_id, display_value=intent.name),
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


def _connected_content_payload(
    *,
    intent: CatalogItemIntent,
    context: CatalogResolvedContext,
    relation_sys_id: str,
    catalog_item_sys_id: str,
    update_name: str,
) -> str:
    return record_update(
        container_element(
            "m2m_connected_content",
            text_element("catalog_item", catalog_item_sys_id, display_value=intent.name),
            text_element("content_display_value", intent.name),
            text_element(
                "content_type",
                context.content_type.sys_id,
                display_value=context.content_type.display,
            ),
            "<source>Jedi DevProject</source>",
            "<sys_class_name>m2m_connected_content</sys_class_name>",
            text_element("sys_id", relation_sys_id),
            SYS_SCOPE_GLOBAL,
            text_element("sys_update_name", update_name),
            text_element("topic", context.topic.sys_id, display_value=context.topic.display),
            action="INSERT_OR_UPDATE",
        ),
        table="m2m_connected_content",
    )


def _reference_variable_payload(variable: CatalogVariableIntent) -> str:
    if variable.variable_type != "reference":
        return ""
    return reference_qualifier_elements(
        reference_table=variable.reference_table or "",
        reference_qualifier=variable.reference_qualifier or "",
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
        sys_id=_required_metadata_reference_value(matches[0].get("sys_id")),
        display=_display_from_record(matches[0], name_fields),
    )


def _catalog_metadata_records(records: object) -> list[dict[str, Any]]:
    if type(records) is not list:
        raise ValueError(CATALOG_ITEM_FIELD_NON_JSON_DIAGNOSTIC)
    for record in records:
        if type(record) is not dict:
            raise ValueError(CATALOG_ITEM_FIELD_NON_JSON_DIAGNOSTIC)
    return records


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
        sys_id=_required_metadata_reference_value(matches[0].get("sys_id")),
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
        sys_id=_required_metadata_reference_value(matches[0].get("sys_id")),
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


def _stable_sys_id(*parts: str) -> str:
    payload = "|".join(parts)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:32]


def _is_active(record: dict[str, Any]) -> bool:
    return _catalog_field_text(record.get("active", "true")).strip().lower() not in {
        "false",
        "0",
        "no",
    }


def _display_from_record(record: dict[str, Any], fields: tuple[str, ...]) -> str:
    for field in fields:
        value = _catalog_first_text(record.get(field)).strip()
        if value:
            return value
    return _reference_value(record.get("sys_id"))


def _normalize_display(value: Any) -> str:
    return _catalog_first_text(value).strip().casefold()


def _reference_value(value: Any) -> str:
    if type(value) is dict:
        return _catalog_first_text(value.get("value"), value.get("display_value"))
    return _catalog_first_text(value)


def _required_metadata_reference_value(value: Any) -> str:
    text = _reference_value(value)
    if text == "":
        raise ValueError(CATALOG_ITEM_METADATA_MISSING_DIAGNOSTIC)
    return text


def _catalog_first_text(*values: Any) -> str:
    for value in values:
        text = _catalog_field_text(value)
        if text:
            return text
    return ""


def _catalog_field_text(value: Any) -> str:
    if value is None:
        return ""
    if type(value) is str:
        return value
    if type(value) is bool or type(value) is int:
        return str(value)
    raise ValueError(CATALOG_ITEM_FIELD_NON_JSON_DIAGNOSTIC)
