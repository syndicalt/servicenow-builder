"""Deterministic ATF test candidate generation from Update Set candidates.

This module maps a validated :class:`UpdateSetCandidate`'s structured changes
to a typed :class:`AtfTestPlan` describing proposed ``sys_atf_test`` and
ordered ``sys_atf_step`` records. The plan is a reviewable candidate-level
artifact (schema ``atf-test-plan-v1``) that downstream tooling can render to
update-set XML once ``sys_atf_*`` XML shape evidence exists; following the
project's evidence-before-XML pattern, no XML is produced here.

Only declarative out-of-box ATF step configs are proposed (never scripted
steps such as "Run Server Side Script"). Step configs are referenced by their
out-of-box display name plus a deterministic placeholder sys_id, because real
``sys_atf_step_config`` sys_ids are instance-version-sensitive; every plan
records those assumptions in ``evidence_assumptions`` so UAT can confirm them
before any XML rendering.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from typing import Any, Final, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from jedi_devproject.models import CandidateChange, UpdateSetCandidate
from jedi_devproject.validation_helpers import stable_record_sys_id

ATF_TEST_PLAN_SCHEMA_VERSION: Final = "atf-test-plan-v1"
ATF_GENERATION_FIELD_NON_JSON_DIAGNOSTIC: Final = (
    "ATF test plan generation field contains non-JSON value"
)

# Declarative out-of-box ATF step config display names this generator assumes.
# These are sys_atf_step_config records whose sys_ids vary by instance
# version; the placeholder sys_ids below are deterministic stand-ins that a
# later XML-rendering pass must resolve against confirmed instance evidence.
STEP_CONFIG_OPEN_NEW_FORM = "Open a New Form"
STEP_CONFIG_SET_FIELD_VALUES = "Set Field Values"
STEP_CONFIG_FIELD_STATE_VALIDATION = "Field State Validation"
STEP_CONFIG_RECORD_VALIDATION = "Record Validation"
STEP_CONFIG_RECORD_INSERT = "Record Insert"
STEP_CONFIG_RECORD_UPDATE = "Record Update"
STEP_CONFIG_OPEN_CATALOG_ITEM = "Open a Catalog Item"
STEP_CONFIG_SET_VARIABLE_VALUES = "Set Variable Values"
STEP_CONFIG_VARIABLE_STATE_VALIDATION = "Variable State Validation"

# Stable reason codes for changes the generator cannot cover. Reviewers and
# downstream tooling key off these codes, so they must never change silently.
REASON_UNSUPPORTED_TABLE = "unsupported_table"
REASON_UNSUPPORTED_OPERATION = "unsupported_operation"
REASON_MISSING_REQUIRED_FIELDS = "missing_required_fields"
REASON_POLICY_ACTION_WITHOUT_POLICY = "policy_action_without_policy"
REASON_FORM_PLACEMENT_WITHOUT_DICTIONARY_INSERT = "form_placement_without_dictionary_insert"
REASON_VARIABLE_WITHOUT_CATALOG_ITEM = "variable_without_catalog_item"

_FORM_PLACEMENT_TABLES = frozenset({"sys_ui_element", "sys_ui_form"})
_TRISTATE_TRUE = "true"
_TRISTATE_FALSE = "false"
_EQUALITY_CONDITION_PATTERN = re.compile(
    r"^(?P<field>[a-z][a-z0-9_.]*)=(?P<value>[^!=<>].*)?$"
)


class AtfStepCandidate(BaseModel):
    """One proposed ``sys_atf_step`` record inside a proposed test."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    sys_id: str
    order: int = Field(ge=1)
    step_config_name: str
    step_config_sys_id_assumption: str
    description: str
    inputs: dict[str, Any] = Field(default_factory=dict)

    @field_validator("sys_id", "step_config_name", "description")
    @classmethod
    def require_non_empty_text(cls, value: str) -> str:
        if value.strip() == "":
            raise ValueError("must not be empty")
        return value


class AtfTestCandidate(BaseModel):
    """One proposed ``sys_atf_test`` record with its ordered steps."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    sys_id: str
    name: str
    description: str
    active: bool = True
    steps: list[AtfStepCandidate]

    @field_validator("sys_id", "name", "description")
    @classmethod
    def require_non_empty_text(cls, value: str) -> str:
        if value.strip() == "":
            raise ValueError("must not be empty")
        return value


class AtfNotCoveredChange(BaseModel):
    """A candidate change the generator explicitly declines to cover."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    table: str
    operation: str
    reason_code: str
    detail: str


class AtfTestPlan(BaseModel):
    """Reviewable ATF test plan derived from one Update Set candidate."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    schema_version: Literal["atf-test-plan-v1"] = ATF_TEST_PLAN_SCHEMA_VERSION
    story_number: str
    candidate_name: str
    tests: list[AtfTestCandidate] = Field(default_factory=list)
    not_covered: list[AtfNotCoveredChange] = Field(default_factory=list)
    evidence_assumptions: list[str] = Field(default_factory=list)


def step_config_sys_id_assumption(step_config_name: str) -> str:
    """Deterministic placeholder sys_id for an assumed OOB step config."""
    return stable_record_sys_id("sys_atf_step_config", step_config_name)


def generate_atf_test_plan(candidate: UpdateSetCandidate) -> AtfTestPlan | None:
    """Map a validated candidate's changes to a deterministic ATF test plan.

    Returns ``None`` when the candidate carries no structured changes at all
    (there is nothing to derive a test from); otherwise every change is either
    covered by a proposed test or listed in ``not_covered`` with a stable
    reason code — changes are never silently skipped.
    """
    if not candidate.changes:
        return None

    builder = _PlanBuilder(candidate)
    builder.build()
    return AtfTestPlan(
        story_number=candidate.story_number,
        candidate_name=candidate.name,
        tests=builder.tests,
        not_covered=builder.not_covered,
        evidence_assumptions=builder.evidence_assumptions(),
    )


class _StepFactory:
    """Builds ordered steps with deterministic sys_ids for one test."""

    def __init__(self, test_name: str) -> None:
        self._test_name = test_name
        self._steps: list[AtfStepCandidate] = []

    @property
    def steps(self) -> list[AtfStepCandidate]:
        return self._steps

    def add(
        self,
        *,
        step_config_name: str,
        description: str,
        inputs: dict[str, Any],
    ) -> AtfStepCandidate:
        order = len(self._steps) + 1
        step = AtfStepCandidate(
            sys_id=stable_record_sys_id(
                "sys_atf_step", self._test_name, str(order), step_config_name
            ),
            order=order,
            step_config_name=step_config_name,
            step_config_sys_id_assumption=step_config_sys_id_assumption(step_config_name),
            description=description,
            inputs=inputs,
        )
        self._steps.append(step)
        return step


class _PlanBuilder:
    def __init__(self, candidate: UpdateSetCandidate) -> None:
        self._candidate = candidate
        self.tests: list[AtfTestCandidate] = []
        self.not_covered: list[AtfNotCoveredChange] = []
        self._extra_assumptions: list[str] = []
        self._consumed: set[int] = set()

    def build(self) -> None:
        changes = self._candidate.changes
        for index, change in enumerate(changes):
            if index in self._consumed:
                continue
            handler = _CHANGE_HANDLERS.get(change.table)
            if handler is None:
                self._record_not_covered(
                    change,
                    reason_code=REASON_UNSUPPORTED_TABLE,
                    detail=f"no ATF mapping exists for table {change.table}",
                )
                continue
            handler(self, index, change)

    # -- change handlers -------------------------------------------------

    def _handle_dictionary(self, index: int, change: CandidateChange) -> None:
        if change.operation != "insert":
            self._record_not_covered(
                change,
                reason_code=REASON_UNSUPPORTED_OPERATION,
                detail="only sys_dictionary insert (new field) is supported",
            )
            return
        target_table = _text(change.fields, "name", "table")
        element = _text(change.fields, "element", "field")
        if not target_table or not element:
            self._record_not_covered(
                change,
                reason_code=REASON_MISSING_REQUIRED_FIELDS,
                detail="sys_dictionary insert requires name (table) and element (field)",
            )
            return
        test_name = f"ATF {self._candidate.story_number} field {target_table}.{element}"
        factory = _StepFactory(test_name)
        factory.add(
            step_config_name=STEP_CONFIG_RECORD_VALIDATION,
            description=(
                f"Server-side: assert the dictionary record for {target_table}.{element} "
                "exists (field is defined on the table)."
            ),
            inputs={
                "execution_context": "server",
                "table": "sys_dictionary",
                "record_conditions": f"name={target_table}^element={element}",
                "assert_type": "record_validated",
            },
        )
        placement = self._consume_form_placement(target_table=target_table, element=element)
        if placement is not None:
            factory.add(
                step_config_name=STEP_CONFIG_OPEN_NEW_FORM,
                description=f"Open a new {target_table} form in the default view.",
                inputs={
                    "execution_context": "client",
                    "table": target_table,
                    "view": "default",
                },
            )
            factory.add(
                step_config_name=STEP_CONFIG_FIELD_STATE_VALIDATION,
                description=(
                    f"Assert {element} is visible on the {target_table} form after placement."
                ),
                inputs={
                    "execution_context": "client",
                    "table": target_table,
                    "field_states": {element: {"visible": True}},
                },
            )
        self._add_test(
            test_name=test_name,
            description=(
                f"Validates the new field {target_table}.{element} proposed by candidate "
                f"{self._candidate.name}."
            ),
            factory=factory,
        )

    def _handle_form_placement(self, index: int, change: CandidateChange) -> None:
        # Form placement changes are consumed alongside the sys_dictionary
        # insert they accompany (see _handle_dictionary); a placement change
        # reaching this handler has no matching field insert in the candidate.
        self._record_not_covered(
            change,
            reason_code=REASON_FORM_PLACEMENT_WITHOUT_DICTIONARY_INSERT,
            detail=(
                "form placement changes are only testable alongside the "
                "sys_dictionary insert they place"
            ),
        )

    def _handle_ui_policy(self, index: int, change: CandidateChange) -> None:
        if change.operation != "insert":
            self._record_not_covered(
                change,
                reason_code=REASON_UNSUPPORTED_OPERATION,
                detail="only sys_ui_policy insert is supported",
            )
            return
        target_table = _text(change.fields, "table", "target_table")
        policy_name = _text(change.fields, "short_description", "policy_name", "name")
        actions = self._consume_actions("sys_ui_policy_action")
        if not target_table or not policy_name or not actions:
            self._record_not_covered(
                change,
                reason_code=REASON_MISSING_REQUIRED_FIELDS,
                detail=(
                    "sys_ui_policy requires a target table, a policy name, and at "
                    "least one sys_ui_policy_action change"
                ),
            )
            return
        conditions = _text(change.fields, "conditions", "condition", "filter_condition")
        test_name = f"ATF {self._candidate.story_number} ui policy {policy_name}"
        factory = _StepFactory(test_name)
        factory.add(
            step_config_name=STEP_CONFIG_OPEN_NEW_FORM,
            description=f"Open a new {target_table} form in the default view.",
            inputs={"execution_context": "client", "table": target_table, "view": "default"},
        )
        self._add_condition_trigger_step(
            factory=factory,
            conditions=conditions,
            target_table=target_table,
            step_config_name=STEP_CONFIG_SET_FIELD_VALUES,
            values_key="field_values",
            context=f"UI policy {policy_name}",
        )
        field_states = _action_states(actions, name_keys=("field", "element"))
        factory.add(
            step_config_name=STEP_CONFIG_FIELD_STATE_VALIDATION,
            description=(
                f"Assert the field states declared by UI policy {policy_name} on "
                f"{target_table}."
            ),
            inputs={
                "execution_context": "client",
                "table": target_table,
                "field_states": field_states,
            },
        )
        self._add_test(
            test_name=test_name,
            description=(
                f"Validates UI policy {policy_name} on {target_table} proposed by "
                f"candidate {self._candidate.name}."
            ),
            factory=factory,
        )

    def _handle_catalog_ui_policy(self, index: int, change: CandidateChange) -> None:
        if change.operation != "insert":
            self._record_not_covered(
                change,
                reason_code=REASON_UNSUPPORTED_OPERATION,
                detail="only catalog_ui_policy insert is supported",
            )
            return
        policy_name = _text(change.fields, "short_description", "policy_name", "name")
        catalog_item = self._catalog_item_name() or _text(
            change.fields, "catalog_item", "cat_item"
        )
        actions = self._consume_actions("catalog_ui_policy_action")
        if not policy_name or not catalog_item or not actions:
            self._record_not_covered(
                change,
                reason_code=REASON_MISSING_REQUIRED_FIELDS,
                detail=(
                    "catalog_ui_policy requires a policy name, a resolvable catalog "
                    "item, and at least one catalog_ui_policy_action change"
                ),
            )
            return
        conditions = _text(
            change.fields, "catalog_conditions", "conditions", "condition"
        )
        test_name = f"ATF {self._candidate.story_number} catalog ui policy {policy_name}"
        factory = _StepFactory(test_name)
        factory.add(
            step_config_name=STEP_CONFIG_OPEN_CATALOG_ITEM,
            description=f"Open the catalog item {catalog_item}.",
            inputs={"execution_context": "client", "catalog_item": catalog_item},
        )
        self._add_condition_trigger_step(
            factory=factory,
            conditions=conditions,
            target_table=catalog_item,
            step_config_name=STEP_CONFIG_SET_VARIABLE_VALUES,
            values_key="variable_values",
            context=f"catalog UI policy {policy_name}",
        )
        variable_states = _action_states(actions, name_keys=("variable", "field"))
        factory.add(
            step_config_name=STEP_CONFIG_VARIABLE_STATE_VALIDATION,
            description=(
                f"Assert the variable states declared by catalog UI policy "
                f"{policy_name} on {catalog_item}."
            ),
            inputs={
                "execution_context": "client",
                "catalog_item": catalog_item,
                "variable_states": variable_states,
            },
        )
        self._add_test(
            test_name=test_name,
            description=(
                f"Validates catalog UI policy {policy_name} on catalog item "
                f"{catalog_item} proposed by candidate {self._candidate.name}."
            ),
            factory=factory,
        )

    def _handle_catalog_item(self, index: int, change: CandidateChange) -> None:
        if change.operation != "insert":
            self._record_not_covered(
                change,
                reason_code=REASON_UNSUPPORTED_OPERATION,
                detail="only sc_cat_item insert is supported",
            )
            return
        item_name = _text(change.fields, "name", "short_description")
        if not item_name:
            self._record_not_covered(
                change,
                reason_code=REASON_MISSING_REQUIRED_FIELDS,
                detail="sc_cat_item insert requires a name",
            )
            return
        variables = self._consume_catalog_variables()
        test_name = f"ATF {self._candidate.story_number} catalog item {item_name}"
        factory = _StepFactory(test_name)
        factory.add(
            step_config_name=STEP_CONFIG_OPEN_CATALOG_ITEM,
            description=f"Open the catalog item {item_name}.",
            inputs={"execution_context": "client", "catalog_item": item_name},
        )
        if variables:
            variable_states: dict[str, dict[str, bool]] = {}
            for variable_change in variables:
                variable_name = _text(variable_change.fields, "name", "variable", "element")
                if not variable_name:
                    self._record_not_covered(
                        variable_change,
                        reason_code=REASON_MISSING_REQUIRED_FIELDS,
                        detail="item_option_new requires a variable name",
                    )
                    continue
                states: dict[str, bool] = {"visible": True}
                if _atf_bool_value(variable_change.fields.get("mandatory")):
                    states["mandatory"] = True
                variable_states[variable_name] = states
            if variable_states:
                factory.add(
                    step_config_name=STEP_CONFIG_VARIABLE_STATE_VALIDATION,
                    description=(
                        f"Assert the catalog item variables on {item_name} are present "
                        "with their declared states."
                    ),
                    inputs={
                        "execution_context": "client",
                        "catalog_item": item_name,
                        "variable_states": variable_states,
                    },
                )
        self._add_test(
            test_name=test_name,
            description=(
                f"Validates catalog item {item_name} proposed by candidate "
                f"{self._candidate.name}."
            ),
            factory=factory,
        )

    def _handle_catalog_variable(self, index: int, change: CandidateChange) -> None:
        # item_option_new changes are consumed alongside their sc_cat_item
        # insert (see _handle_catalog_item); one reaching this handler has no
        # catalog item change in the candidate to anchor the test on.
        self._record_not_covered(
            change,
            reason_code=REASON_VARIABLE_WITHOUT_CATALOG_ITEM,
            detail=(
                "catalog variables are only testable alongside the sc_cat_item "
                "insert that owns them"
            ),
        )

    def _handle_policy_action(self, index: int, change: CandidateChange) -> None:
        # Policy actions are consumed alongside their owning policy change;
        # one reaching this handler is orphaned within the candidate.
        self._record_not_covered(
            change,
            reason_code=REASON_POLICY_ACTION_WITHOUT_POLICY,
            detail=(
                f"{change.table} changes are only testable alongside the policy "
                "insert that owns them"
            ),
        )

    def _handle_business_rule(self, index: int, change: CandidateChange) -> None:
        if change.operation != "insert":
            self._record_not_covered(
                change,
                reason_code=REASON_UNSUPPORTED_OPERATION,
                detail="only sys_script insert is supported",
            )
            return
        target_table = _text(change.fields, "collection", "table")
        rule_name = _text(change.fields, "name")
        fields_written = _atf_string_list(change.fields.get("fields_written"))
        if not target_table or not rule_name:
            self._record_not_covered(
                change,
                reason_code=REASON_MISSING_REQUIRED_FIELDS,
                detail="sys_script insert requires collection (table) and name",
            )
            return
        if not fields_written:
            self._record_not_covered(
                change,
                reason_code=REASON_MISSING_REQUIRED_FIELDS,
                detail=(
                    "sys_script insert must declare fields_written so the rule "
                    "outcome can be validated declaratively"
                ),
            )
            return
        filter_condition = _text(
            change.fields, "filter_condition", "condition", "conditions", "filter"
        )
        trigger_values, unconverted = _equality_conditions(filter_condition)
        if unconverted:
            self._extra_assumptions.append(
                f"Business rule {rule_name}: filter condition terms "
                f"{', '.join(unconverted)} could not be converted to declarative "
                "trigger values; the reviewer must extend the record steps so the "
                "rule's condition is met."
            )
        runs_on_insert = (
            _atf_bool_value(change.fields.get("action_insert"))
            or _atf_bool_value(change.fields.get("insert"))
            or _atf_bool_value(change.fields.get("operation_insert"))
        )
        runs_on_update = (
            _atf_bool_value(change.fields.get("action_update"))
            or _atf_bool_value(change.fields.get("update"))
            or _atf_bool_value(change.fields.get("operation_update"))
        )
        test_name = f"ATF {self._candidate.story_number} business rule {rule_name}"
        factory = _StepFactory(test_name)
        insert_step = factory.add(
            step_config_name=STEP_CONFIG_RECORD_INSERT,
            description=(
                f"Server-side: insert a {target_table} record"
                + (" matching the rule's trigger condition." if trigger_values else ".")
            ),
            inputs={
                "execution_context": "server",
                "table": target_table,
                "field_values": trigger_values,
            },
        )
        mutation_step = insert_step
        if runs_on_update and not runs_on_insert:
            mutation_step = factory.add(
                step_config_name=STEP_CONFIG_RECORD_UPDATE,
                description=(
                    f"Server-side: update the inserted {target_table} record so the "
                    "update-timing rule fires."
                ),
                inputs={
                    "execution_context": "server",
                    "table": target_table,
                    "record_source_step_sys_id": insert_step.sys_id,
                    "field_values": trigger_values,
                },
            )
        factory.add(
            step_config_name=STEP_CONFIG_RECORD_VALIDATION,
            description=(
                f"Server-side: assert business rule {rule_name} wrote its declared "
                f"fields ({', '.join(fields_written)})."
            ),
            inputs={
                "execution_context": "server",
                "table": target_table,
                "record_source_step_sys_id": mutation_step.sys_id,
                "record_conditions": "^".join(
                    f"{field}ISNOTEMPTY" for field in fields_written
                ),
                "assert_type": "record_validated",
            },
        )
        self._add_test(
            test_name=test_name,
            description=(
                f"Validates business rule {rule_name} on {target_table} proposed by "
                f"candidate {self._candidate.name}."
            ),
            factory=factory,
        )

    # -- helpers ----------------------------------------------------------

    def _add_condition_trigger_step(
        self,
        *,
        factory: _StepFactory,
        conditions: str,
        target_table: str,
        step_config_name: str,
        values_key: str,
        context: str,
    ) -> None:
        trigger_values, unconverted = _equality_conditions(conditions)
        if unconverted:
            self._extra_assumptions.append(
                f"{context}: condition terms {', '.join(unconverted)} could not be "
                "converted to declarative trigger values; the reviewer must extend "
                "the trigger step so the policy condition is met."
            )
        if not trigger_values:
            return
        factory.add(
            step_config_name=step_config_name,
            description=f"Set the values that satisfy the {context} condition.",
            inputs={
                "execution_context": "client",
                "table": target_table,
                values_key: trigger_values,
            },
        )

    def _consume_form_placement(
        self, *, target_table: str, element: str
    ) -> CandidateChange | None:
        for index, change in enumerate(self._candidate.changes):
            if index in self._consumed or change.table not in _FORM_PLACEMENT_TABLES:
                continue
            change_table = _text(change.fields, "table", "name")
            change_field = _text(change.fields, "field", "element")
            if change_table == target_table and change_field in {element, ""}:
                self._consumed.add(index)
                return change
        return None

    def _consume_actions(self, action_table: str) -> list[CandidateChange]:
        actions: list[CandidateChange] = []
        for index, change in enumerate(self._candidate.changes):
            if index in self._consumed or change.table != action_table:
                continue
            self._consumed.add(index)
            actions.append(change)
        return actions

    def _consume_catalog_variables(self) -> list[CandidateChange]:
        return self._consume_actions("item_option_new")

    def _catalog_item_name(self) -> str:
        for change in self._candidate.changes:
            if change.table == "sc_cat_item":
                return _text(change.fields, "name", "short_description")
        return ""

    def _add_test(self, *, test_name: str, description: str, factory: _StepFactory) -> None:
        self.tests.append(
            AtfTestCandidate(
                sys_id=stable_record_sys_id(
                    "sys_atf_test", self._candidate.story_number, test_name
                ),
                name=test_name,
                description=description,
                steps=factory.steps,
            )
        )

    def _record_not_covered(
        self,
        change: CandidateChange,
        *,
        reason_code: str,
        detail: str,
    ) -> None:
        self.not_covered.append(
            AtfNotCoveredChange(
                table=change.table,
                operation=change.operation,
                reason_code=reason_code,
                detail=detail,
            )
        )

    def evidence_assumptions(self) -> list[str]:
        step_config_names = sorted(
            {step.step_config_name for test in self.tests for step in test.steps}
        )
        assumptions = [
            (
                f"ATF step config '{name}' is assumed to exist as an out-of-box "
                "sys_atf_step_config record on the target instance; its sys_id is "
                "instance-version-sensitive, so the deterministic placeholder "
                f"'{step_config_sys_id_assumption(name)}' must be replaced with the "
                "instance's confirmed sys_id (UAT evidence) before XML rendering."
            )
            for name in step_config_names
        ]
        if self.tests:
            assumptions.append(
                "Step input field names (table, field_values, field_states, "
                "record_conditions, variable_states) describe the declarative "
                "intent of each step; the exact sys_atf_step input variable "
                "contract per step config must be confirmed against instance "
                "evidence before XML rendering."
            )
        assumptions.extend(self._extra_assumptions)
        return assumptions


def _text(fields: dict[str, Any], *keys: str) -> str:
    for key in keys:
        value = _atf_field_text(fields.get(key)).strip()
        if value:
            return value
    return ""


def _atf_string_list(value: Any, *, ignore_none_token: bool = False) -> list[str]:
    if type(value) is list:
        return [text for item in value if (text := _atf_field_text(item).strip())]
    text = _atf_field_text(value).strip()
    if not text or (ignore_none_token and text.lower() == "none"):
        return []
    return [item.strip() for item in text.split(",") if item.strip()]


def _atf_bool_value(value: Any, *, default: bool = False) -> bool:
    if value is None:
        return default
    return _atf_field_text(value).strip().lower() in {"1", "true", "yes", "y"}


def _atf_field_text(value: Any) -> str:
    if value is None:
        return ""
    if type(value) is str:
        return value
    if type(value) is bool or type(value) is int:
        return str(value)
    raise ValueError(ATF_GENERATION_FIELD_NON_JSON_DIAGNOSTIC)


def _action_states(
    actions: list[CandidateChange],
    *,
    name_keys: tuple[str, ...],
) -> dict[str, dict[str, bool]]:
    states: dict[str, dict[str, bool]] = {}
    for action in actions:
        name = _text(action.fields, *name_keys)
        if not name:
            continue
        action_states: dict[str, bool] = {}
        for state_name, field_keys in (
            ("visible", ("visible",)),
            ("mandatory", ("mandatory",)),
            ("read_only", ("disabled", "read_only")),
        ):
            tristate = _tristate(action.fields, *field_keys)
            if tristate == _TRISTATE_TRUE:
                action_states[state_name] = True
            elif tristate == _TRISTATE_FALSE:
                action_states[state_name] = False
        if action_states:
            states[name] = action_states
    return states


def _tristate(fields: dict[str, Any], *keys: str) -> str:
    for key in keys:
        value = _atf_field_text(fields.get(key)).strip().lower()
        if value in {_TRISTATE_TRUE, _TRISTATE_FALSE}:
            return value
    return "ignore"


def _equality_conditions(conditions: str) -> tuple[dict[str, str], list[str]]:
    """Split an encoded query into declarative equality values.

    Returns ``(values, unconverted_terms)``. Only AND-joined ``field=value``
    terms become trigger values; OR branches, non-equality operators, and the
    ``EQ`` terminator are reported (or dropped, for ``EQ``) so nothing is
    converted incorrectly.
    """
    cleaned = conditions.strip()
    if not cleaned:
        return {}, []
    values: dict[str, str] = {}
    unconverted: list[str] = []
    for index, raw_term in enumerate(cleaned.split("^")):
        term = raw_term.strip()
        if not term or term == "EQ":
            continue
        if index > 0 and term.startswith("OR"):
            unconverted.append(term)
            continue
        match = _EQUALITY_CONDITION_PATTERN.fullmatch(term)
        if match is None or not (match.group("value") or "").strip():
            unconverted.append(term)
            continue
        values[match.group("field")] = (match.group("value") or "").strip()
    return values, unconverted


_CHANGE_HANDLERS: dict[str, Callable[[_PlanBuilder, int, CandidateChange], None]] = {
    "sys_dictionary": _PlanBuilder._handle_dictionary,
    "sys_ui_element": _PlanBuilder._handle_form_placement,
    "sys_ui_form": _PlanBuilder._handle_form_placement,
    "sys_ui_policy": _PlanBuilder._handle_ui_policy,
    "sys_ui_policy_action": _PlanBuilder._handle_policy_action,
    "catalog_ui_policy": _PlanBuilder._handle_catalog_ui_policy,
    "catalog_ui_policy_action": _PlanBuilder._handle_policy_action,
    "sc_cat_item": _PlanBuilder._handle_catalog_item,
    "item_option_new": _PlanBuilder._handle_catalog_variable,
    "sys_script": _PlanBuilder._handle_business_rule,
}
