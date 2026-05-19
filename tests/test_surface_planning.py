from jedi_devproject.automation_intent import (
    AutomationIntent,
    AutomationIntentSource,
    AutomationIntentType,
)
from jedi_devproject.capabilities import Capability
from jedi_devproject.surface_planning import (
    ServiceNowSurface,
    SurfaceOperationKind,
    SurfaceOperationStatus,
    plan_surface_operations,
)


def test_plans_form_section_remove_as_supported_surface_operation() -> None:
    plan = plan_surface_operations(
        AutomationIntent(
            source=AutomationIntentSource.STRUCTURED,
            intent_type=AutomationIntentType.FORM_SECTION,
            capability=Capability.FORM_SECTION_REMOVE,
            target_table="dmn_demand",
            form_view="Default view",
            form_sections=["Assessment", "Financials"],
            expected_behavior="Hide the Assessment and Financials tabs.",
            required_instance_context=["form_sections", "form_layout"],
        )
    )

    assert plan.surface is ServiceNowSurface.FORM_LAYOUT
    assert plan.target_table == "dmn_demand"
    assert plan.required_instance_context == ["form_sections", "form_layout"]
    assert plan.operations[0].kind is SurfaceOperationKind.FORM_LAYOUT_SECTION_REMOVE
    assert plan.operations[0].status is SurfaceOperationStatus.SUPPORTED
    assert plan.operations[0].view == "Default view"
    assert plan.operations[0].targets == ["Assessment", "Financials"]


def test_plans_form_section_rename_as_unsupported_operation_without_delete() -> None:
    plan = plan_surface_operations(
        AutomationIntent(
            source=AutomationIntentSource.STRUCTURED,
            intent_type=AutomationIntentType.FORM_SECTION,
            capability=Capability.UNKNOWN,
            target_table="dmn_demand",
            form_view="Default view",
            form_sections=["Financials"],
            expected_behavior="Rename the Financials tab to Budget Details.",
            required_instance_context=["form_sections", "form_layout"],
        )
    )

    assert plan.surface is ServiceNowSurface.FORM_LAYOUT
    assert plan.operations[0].kind is SurfaceOperationKind.FORM_LAYOUT_SECTION_RENAME
    assert plan.operations[0].status is SurfaceOperationStatus.UNSUPPORTED
    assert "builder_not_implemented" in plan.operations[0].reason_codes


def test_plans_form_section_add_and_reorder_as_known_unsupported_operations() -> None:
    add_plan = plan_surface_operations(
        AutomationIntent(
            source=AutomationIntentSource.STRUCTURED,
            intent_type=AutomationIntentType.FORM_SECTION,
            capability=Capability.UNKNOWN,
            target_table="incident",
            form_sections=["Vendor Details"],
            expected_behavior="Add a Vendor Details tab to the Incident form.",
        )
    )
    reorder_plan = plan_surface_operations(
        AutomationIntent(
            source=AutomationIntentSource.STRUCTURED,
            intent_type=AutomationIntentType.FORM_SECTION,
            capability=Capability.UNKNOWN,
            target_table="incident",
            form_sections=["Resolution Information"],
            expected_behavior="Move the Resolution Information tab before Notes.",
        )
    )

    assert add_plan.operations[0].kind is SurfaceOperationKind.FORM_LAYOUT_SECTION_ADD
    assert add_plan.operations[0].status is SurfaceOperationStatus.UNSUPPORTED
    assert reorder_plan.operations[0].kind is SurfaceOperationKind.FORM_LAYOUT_SECTION_REORDER
    assert reorder_plan.operations[0].status is SurfaceOperationStatus.UNSUPPORTED
